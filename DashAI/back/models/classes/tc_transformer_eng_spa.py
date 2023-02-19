import json
import os

import evaluate
import numpy as np
from transformers import (
    AutoModelForSeq2SeqLM,
    AutoTokenizer,
    DataCollatorForSeq2Seq,
    Seq2SeqTrainer,
    Seq2SeqTrainingArguments,
)

from DashAI.back.datasets import Dataset
from DashAI.back.models.classes.translation_model import TranslationModel


class tcTransformerEngSpa(TranslationModel):
    """
    Transformer pre-trained from Tatoeba Challenge used for translating
    from english sentences to spanish.
    """

    MODEL = "tcTransformerEngSpa"
    with open(f"Models/parameters/models_schemas/{MODEL}.json") as f:
        SCHEMA = json.load(f)

    def __init__(self, **kwargs) -> None:
        self.model_name = "Helsinki-NLP/opus-mt-en-es"
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.model = AutoModelForSeq2SeqLM.from_pretrained(self.model_name)
        self.source = "English"
        self.target = "Spanish"
        self.batch_size = kwargs.pop("batch_size")  # 16
        self.epochs = kwargs.pop("epochs")  # 1
        self.weight_decay = kwargs.pop("weight_decay")  # 0.01
        self.learning_rate = kwargs.pop("learning_rate")  # 2e-5
        self.device = kwargs.pop("device")  # gpu
        self.path = (
            str(self.model_name.split("/")[-1])
            + f"-finetuned-{self.source}-to-{self.target}"
        )
        self.args = Seq2SeqTrainingArguments(
            self.path,
            evaluation_strategy="epoch",
            learning_rate=self.learning_rate,
            per_device_train_batch_size=self.batch_size,
            per_device_eval_batch_size=self.batch_size,
            weight_decay=self.weight_decay,
            save_total_limit=1,
            num_train_epochs=self.epochs,
            predict_with_generate=True,
            no_cuda=False if self.device == "gpu" else True,
        )
        self.data_collator = DataCollatorForSeq2Seq(self.tokenizer, model=self.model)
        self.metric_bleu = evaluate.load("sacrebleu")
        self.metric_ter = evaluate.load("ter")

    def tokenize_input(self, d):
        """
        Function to tokenize the input, d should be a DatasetDict
        """
        model_inputs = self.tokenizer(d["source_text"], truncation=True)
        labels = self.tokenizer(text_target=d["target_text"], truncation=True)
        model_inputs["labels"] = labels["input_ids"]
        return model_inputs

    def tokenize_aux(self, d):
        """
        Function to tokenize the whole dataset, d should be a DatasetDict
        """
        return d.map(self.tokenize_input, batched=True)

    def postprocess_text(self, preds, labels):
        """
        Function for text processing in the compute_metrics function
        """
        preds = [pred.strip() for pred in preds]
        labels = [[label.strip()] for label in labels]
        return preds, labels

    def compute_metrics(self, eval_preds):
        """
        Function to compute metrics in evaluation dataset
        """
        preds, labels = eval_preds
        if isinstance(preds, tuple):
            preds = preds[0]
        decoded_preds = self.tokenizer.batch_decode(preds, skip_special_tokens=True)
        # Replace -100 in the labels as we can't decode them.
        labels = np.where(labels != -100, labels, self.tokenizer.pad_token_id)
        decoded_labels = self.tokenizer.batch_decode(labels, skip_special_tokens=True)
        # Some simple post-processing
        decoded_preds, decoded_labels = self.postprocess_text(
            decoded_preds, decoded_labels
        )
        result_bleu = self.metric_bleu.compute(
            predictions=decoded_preds, references=decoded_labels
        )
        result_ter = self.metric_ter.compute(
            predictions=decoded_preds, references=decoded_labels
        )
        result = {"bleu": result_bleu["score"], "ter": result_ter["score"]}
        return result

    def fit(self, x, y):
        """
        Function to fine-tuning the model
        """
        train_dataset = self.tokenize_aux(
            Dataset.from_dict({"source_text": x, "target_text": y})
        )
        eval_dataset = self.tokenize_aux(
            Dataset.from_dict({"source_text": x, "target_text": y}).select(range(2))
        )
        self.trainer = Seq2SeqTrainer(
            self.model,
            self.args,
            train_dataset=train_dataset,
            eval_dataset=eval_dataset,
            data_collator=self.data_collator,
            tokenizer=self.tokenizer,
            compute_metrics=self.compute_metrics,
        )
        # self.trainer.train()

    def predict(self, x):
        """
        Function to translate a sentence in english x to spanish
        """
        src_text = [x]
        model_name_finetuned = self.path + "/" + os.listdir(self.path)[0]
        tokenizer = AutoTokenizer.from_pretrained(
            model_name_finetuned, local_files_only=True
        )
        model = AutoModelForSeq2SeqLM.from_pretrained(
            model_name_finetuned, local_files_only=True
        )
        translated = model.generate(
            **tokenizer(src_text, return_tensors="pt", padding=True), max_new_tokens=512
        )
        translated = [tokenizer.decode(t, skip_special_tokens=True) for t in translated]
        return translated[0]

    # My name is Sarah and I live in London
    def score(self, x, y):
        """
        Function to calculate model metrics according to the evaluation dataset
        """
        eval_dataset = self.tokenize_aux(
            Dataset.from_dict({"source_text": x, "target_text": y}).select(range(100))
        )
        metrics = self.trainer.evaluate(eval_dataset=eval_dataset)
        return metrics

    def get_params(self):
        """
        Function to get the model parameters
        """
        params_dict = {
            "epochs": self.epochs,
            "batch_size": self.batch_size,
            "weight_decay": self.weight_decay,
            "learning_rate": self.learning_rate,
            "device": self.device,
        }
        return params_dict
