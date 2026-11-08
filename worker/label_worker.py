
import json
import os
import urllib.request
from pathlib import Path

DATASET = Path("data/commands_pool.jsonl")
PROMPT = Path("prompts/teacher_prompt.txt")

SHARD_INDEX = int(os.getenv("SHARD_INDEX", "0"))
SHARD_COUNT = int(os.getenv("SHARD_COUNT", "2"))
MAX_COMMANDS = int(os.getenv("MAX_COMMANDS", "0"))
OLLAMA_URL = os.getenv(
    "OLLAMA_URL", "http://localhost:11434"
)

OUTPUT = Path(f"results/shard-{SHARD_INDEX}.jsonl")


def generate_label(command, prompt):
    payload = {
        "model": "phi3.5",
        "prompt": f"{prompt}\nCommand: {command}\nOutput:",
        "stream": False,
        "format": "json",
        "options": {
            "temperature": 0,
            "seed": 42
        }
    }

    request = urllib.request.Request(
        f"{OLLAMA_URL}/api/generate",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    with urllib.request.urlopen(
        request, timeout=300
    ) as response:
        result = json.load(response)

    return result["response"]


def load_completed_ids():
    completed = set()

    if OUTPUT.exists():
        with OUTPUT.open(encoding="utf-8") as file:
            for line in file:
                if line.strip():
                    record = json.loads(line)
                    completed.add(record["id"])

    return completed


def main():
    if SHARD_COUNT < 1:
        raise ValueError("SHARD_COUNT must be >= 1")

    if not 0 <= SHARD_INDEX < SHARD_COUNT:
        raise ValueError("Invalid SHARD_INDEX")

    prompt = PROMPT.read_text(encoding="utf-8")
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    completed_ids = load_completed_ids()

    print(
        f"Shard {SHARD_INDEX}: "
        f"{len(completed_ids)} existing records"
    )

    processed = 0

    with DATASET.open(encoding="utf-8") as source, \
         OUTPUT.open("a", encoding="utf-8") as target:

        for line_number, line in enumerate(source):
            if line_number % SHARD_COUNT != SHARD_INDEX:
                continue

            item = json.loads(line)

            if item["id"] in completed_ids:
                continue

            if MAX_COMMANDS and processed >= MAX_COMMANDS:
                break

            raw_reply = generate_label(
                item["text"], prompt
            )

            record = {
                "id": item["id"],
                "text": item["text"],
                "teacher_raw": raw_reply
            }

            target.write(
                json.dumps(record, ensure_ascii=False)
                + "\n"
            )
            target.flush()

            completed_ids.add(item["id"])
            processed += 1

            print(
                f"Shard {SHARD_INDEX}: "
                f"{processed} new commands processed",
                flush=True
            )

    print(
        f"Shard {SHARD_INDEX}: "
        f"saved {processed} new records to {OUTPUT}"
    )


if __name__ == "__main__":
    main()
