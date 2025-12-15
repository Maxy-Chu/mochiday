from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    Trainer,
    TrainingArguments,
)
from datasets import load_dataset, Dataset
import torch
from torch.utils.data import Dataset, DataLoader
import pandas as pd


class JobDataset(Dataset):
    def __init__(self, dataframe, tokenizer, max_length=128):
        self.dataframe = dataframe
        self.tokenizer = tokenizer
        self.max_length = max_length
        self.label2id = {"intern": 0, "newgrad": 1, "junior": 2, "mid": 3, "senior": 4}

    def __len__(self):
        return len(self.dataframe)

    def __getitem__(self, idx):
        row = self.dataframe.iloc[idx]
        text = (row["title"] + ". " + row["description"])[:512]  # 只取前512字符
        inputs = self.tokenizer(
            text,
            padding="max_length",
            truncation=True,
            max_length=self.max_length,
            return_tensors="pt",
        )
        label = torch.tensor(self.label2id[row["seniority"]], dtype=torch.long)
        return {
            "input_ids": inputs["input_ids"].squeeze(),
            "attention_mask": inputs["attention_mask"].squeeze(),
            "labels": label,
        }


# --------------------------
# 2. 加载训练数据
# --------------------------
df = pd.read_csv("seniority_train.csv")  # 你的训练集路径
tokenizer = AutoTokenizer.from_pretrained("prajjwal1/bert-tiny")  # TinyBERT

dataset = JobDataset(df, tokenizer)
train_loader = DataLoader(dataset, batch_size=16, shuffle=True)

# --------------------------
# 3. 定义模型
# --------------------------
model = AutoModelForSequenceClassification.from_pretrained(
    "prajjwal1/bert-tiny", num_labels=5
)

# --------------------------
# 4. Trainer 配置
# --------------------------
training_args = TrainingArguments(
    output_dir="./seniority_model",
    num_train_epochs=3,
    per_device_train_batch_size=16,
    save_steps=50,
    save_total_limit=2,
    logging_dir="./logs",
    logging_steps=10,
    learning_rate=5e-5,
    evaluation_strategy="no",
    remove_unused_columns=False,
)

trainer = Trainer(
    model=model, args=training_args, train_dataset=dataset, tokenizer=tokenizer
)

# --------------------------
# 5. 开始训练
# --------------------------
trainer.train()

# --------------------------
# 6. 保存模型
# --------------------------
trainer.save_model("./seniority_model")
tokenizer.save_pretrained("./seniority_model")
