
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM


class ModelRunner:
    def __init__(self, model_path):
        self.model_path = model_path
        self.device = torch.device("cpu")

        self.tokenizer = AutoTokenizer.from_pretrained(
            model_path
        )
        self.tokenizer.pad_token = self.tokenizer.eos_token

        self.model = AutoModelForCausalLM.from_pretrained(
            model_path
        ).to(self.device)

        self.model.eval()

    def predict(self, text, max_new_tokens=80):
        prompt = f"Command: {text}\nJSON:"

        inputs = self.tokenizer(
            prompt, return_tensors="pt"
        ).to(self.device)

        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                do_sample=False,
                pad_token_id=self.tokenizer.eos_token_id
            )

        generated = outputs[0][inputs["input_ids"].shape[1]:]

        return self.tokenizer.decode(
            generated, skip_special_tokens=True
        ).strip()
