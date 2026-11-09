
import argparse
import json
from pathlib import Path

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True)
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    torch.set_num_threads(2)

    tokenizer = AutoTokenizer.from_pretrained(args.model)
    tokenizer.pad_token = tokenizer.eos_token

    model = AutoModelForCausalLM.from_pretrained(
        args.model
    ).to("cpu")
    model.eval()

    records = [
        json.loads(line)
        for line in Path(args.input).read_text(
            encoding="utf-8"
        ).splitlines()
        if line.strip()
    ]

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)

    with output.open("w", encoding="utf-8") as file:
        for i, row in enumerate(records):
            prompt = f"Command: {row['text']}\nJSON:"

            inputs = tokenizer(
                prompt, return_tensors="pt"
            )

            with torch.inference_mode():
                generated = model.generate(
                    **inputs,
                    max_new_tokens=80,
                    do_sample=False,
                    pad_token_id=tokenizer.eos_token_id,
                )

            new_tokens = generated[0][
                inputs["input_ids"].shape[1]:
            ]

            prediction = tokenizer.decode(
                new_tokens,
                skip_special_tokens=True,
            ).strip()

            file.write(json.dumps({
                "id": row["id"],
                "prediction": prediction,
            }) + "\n")

            if (i + 1) % 20 == 0:
                print(
                    f"Evaluated {i + 1}/{len(records)}",
                    flush=True,
                )


if __name__ == "__main__":
    main()
