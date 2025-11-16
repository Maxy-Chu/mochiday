from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch


class TinyBERT:
    def __init__(self):
        # TinyBERT light model
        self.tokenizer = AutoTokenizer.from_pretrained("./seniority_model")
        self.model = AutoModelForSequenceClassification.from_pretrained(
            "./seniority_model"
        )
        self.model.eval()
        self.labels = {0: "intern", 1: "newgrad", 2: "junior", 3: "mid", 4: "senior"}

    def classify(self, title, description) -> str:
        """Method to classify the seniority level based on title and description."""
        text = (title + ". " + description)[:512]
        inputs = self.tokenizer(
            text, return_tensors="pt", truncation=True, padding=True
        )
        with torch.no_grad():
            logits = self.model(**inputs).logits
        pred_id = torch.argmax(logits, dim=1).item()

        return self.labels[pred_id]
