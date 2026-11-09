
import json
import hashlib
from pathlib import Path
from collections import Counter

SOURCE = Path("results")
OUTPUT = Path("data/v1/train.jsonl")
CHECKSUM = Path("data/v1/train.sha256")
REPORT = Path("results/cleaning_report.json")
SCHEMA = Path("data/schema.json")
COMMANDS = Path("data/commands_pool.jsonl")


def read_jsonl(path):
    with path.open("r", encoding="utf-8") as file:
        for line in file:
            if line.strip():
                yield json.loads(line)


def main():
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))

    required_keys = set(schema["keys"])
    allowed_intents = set(schema["intents"])

    # Verify the original dataset.
    source_rows = list(read_jsonl(COMMANDS))
    expected = {row["id"]: row["text"] for row in source_rows}

    if len(expected) != len(source_rows):
        raise ValueError("Duplicate IDs in commands_pool.jsonl")

    # Load both teacher shards.
    rows = []
    for index in (0, 1):
        path = SOURCE / f"shard-{index}.jsonl"

        if not path.exists():
            raise FileNotFoundError(path)

        rows.extend(read_jsonl(path))

    # Verify full coverage before cleaning.
    ids = [row["id"] for row in rows]

    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate command IDs in shards")

    if set(ids) != set(expected):
        missing = set(expected) - set(ids)
        extra = set(ids) - set(expected)
        raise ValueError(
            f"Shard mismatch: missing={len(missing)}, "
            f"extra={len(extra)}"
        )

    for row in rows:
        if row["text"] != expected[row["id"]]:
            raise ValueError(
                f"Text mismatch for {row['id']}"
            )

    # Sort by command ID before filtering.
    rows.sort(key=lambda row: row["id"])

    counts = Counter()
    counts["input"] = len(rows)

    cleaned = []
    seen_commands = set()

    for row in rows:
        raw = row["teacher_raw"]
        command = row["text"]

        # (a) Invalid JSON
        try:
            parsed = json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            counts["invalid_json"] += 1
            continue

        # (b) Incorrect keys or schema types
        if not isinstance(parsed, dict):
            counts["wrong_keys"] += 1
            continue

        if set(parsed.keys()) != required_keys:
            counts["wrong_keys"] += 1
            continue

        # (c) Invalid intent
        if parsed["intent"] not in allowed_intents:
            counts["bad_intent"] += 1
            continue

        # (d) Invented or invalid slot values
        valid_slots = True

        for key in ("date", "time", "place"):
            value = parsed[key]

            if value is None:
                continue

            if not isinstance(value, str):
                valid_slots = False
                break

            if not value or value not in command:
                valid_slots = False
                break

        if not valid_slots:
            counts["invented_slot"] += 1
            continue

        # (e) Duplicate commands
        if command in seen_commands:
            counts["duplicates"] += 1
            continue

        seen_commands.add(command)

        # Preserve the exact teacher output.
        cleaned.append({
            "id": row["id"],
            "text": command,
            "teacher_raw": raw
        })

    counts["kept"] = len(cleaned)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.parent.mkdir(parents=True, exist_ok=True)

    with OUTPUT.open("w", encoding="utf-8") as file:
        for row in cleaned:
            file.write(
                json.dumps(row, ensure_ascii=False)
                + "\n"
            )

    # SHA-256 checksum
    digest = hashlib.sha256(
        OUTPUT.read_bytes()
    ).hexdigest()

    CHECKSUM.write_text(
        f"{digest}  train.jsonl\n",
        encoding="utf-8"
    )

    REPORT.write_text(
        json.dumps(dict(counts), indent=2) + "\n",
        encoding="utf-8"
    )

    assert (
        counts["invalid_json"]
        + counts["wrong_keys"]
        + counts["bad_intent"]
        + counts["invented_slot"]
        + counts["duplicates"]
        + counts["kept"]
        == counts["input"]
    )

    print("\n=== CLEANING REPORT ===")
    for key, value in counts.items():
        print(f"{key}: {value}")

    print(f"\nSHA-256: {digest}")
    print(f"Saved dataset: {OUTPUT}")


if __name__ == "__main__":
    main()
