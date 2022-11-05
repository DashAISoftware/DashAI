import json
from pathlib import Path
from datasets.dataset_dict import DatasetDict
from datasets import Dataset
import numpy as np
from transformers import AutoTokenizer
from transformers import AutoModelForSeq2SeqLM, DataCollatorForSeq2Seq, Seq2SeqTrainingArguments, Seq2SeqTrainer
import evaluate
from Models.classes.translationModel import TranslationModel


class tcTransformerEngSpa(TranslationModel):
    """
    Transformer pre-trained from Tatoeba Challenge used for translating
    from english sentences to spanish.
    """

    MODEL = "TCTransformer"
    with open(f"Models/parameters/models_schemas/{MODEL}.json") as f:
        SCHEMA = json.load(f)

    def __init__(self, **kwargs) -> None:
        self.model_name = "Helsinki-NLP/opus-mt-en-es"
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.model = AutoModelForSeq2SeqLM.from_pretrained(self.model_name)
        self.source = "English"
        self.target = "Spanish"
        self.batch_size = 16
        self.epochs = 1
        self.weight_decay = 0.01
        #self.batch_size = kwargs.pop("batch_size")
        #self.epochs = kwargs.pop("epochs")
        #self.weight_decay = kwargs.pop("weight_decay")
        self.args = Seq2SeqTrainingArguments(
            str(self.model_name.split("/")[-1]) + f"-finetuned-{self.source}-to-{self.target}",
            evaluation_strategy="epoch",
            learning_rate=2e-5,
            per_device_train_batch_size=self.batch_size,
            per_device_eval_batch_size=self.batch_size,
            weight_decay=self.weight_decay,
            save_total_limit=1,
            num_train_epochs=self.epochs,
            predict_with_generate=True
        )
        self.data_collator = DataCollatorForSeq2Seq(self.tokenizer, model=self.model)
        self.metric = evaluate.load("sacrebleu")
        # self.metric_bleu = evaluate.load("sacrebleu")
        # self.metric_ter = evaluate.load("ter")
        # self.metric_meteor = evaluate.load("meteor")

    def tokenize_input(self, d):
        """
        Function to tokenize the input, d should be a DatasetDict
        """
        model_inputs = self.tokenizer(d["source_text"], max_length=128, truncation=True)
        labels = self.tokenizer(text_target=d["target_text"], max_length=128, truncation=True)
        model_inputs["labels"] = labels["input_ids"]
        return model_inputs

    def tokenize_aux(self, d):
        """
        Function to tokenize the whole dataset, d should be a DatasetDict
        """
        return d.map(self.tokenize_input, batched=True)

    def parse_input(self, input_data):
        """
        Function to transform input data to DatasetDict
        """
        d = {'train': Dataset.from_dict(
            {'source_text': input_data["train"]["x"], 'target_text': input_data["train"]["y"]}),
            'test': Dataset.from_dict({'source_text': input_data["test"]["x"],
                                       'target_text': input_data["test"]["y"]})
        }

        d = DatasetDict(d)
        return d

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
        decoded_preds, decoded_labels = self.postprocess_text(decoded_preds, decoded_labels)
        result = self.metric.compute(predictions=decoded_preds, references=decoded_labels)
        result = {"bleu": result["score"]}
        return result

    def fit(self, d):
        """
        Function to fine-tuning the model
        """
        self.trainer = Seq2SeqTrainer(
            self.model,
            self.args,
            train_dataset=d["train"],
            eval_dataset=d["test"].select(range(100)),
            data_collator=self.data_collator,
            tokenizer=self.tokenizer,
            compute_metrics=self.compute_metrics
        )
        # self.trainer.train()

    def predict(self, x):
        """
        Function to translate a sentence in english x to spanish
        """
        src_text = [x]
        model_name_finetuned = 'opus-mt-en-es-finetuned-English-to-Spanish/checkpoint-5500'
        model_name_finetuned = Path(model_name_finetuned).resolve()
        tokenizer = AutoTokenizer.from_pretrained(model_name_finetuned
                                                  , local_files_only=True)
        model = AutoModelForSeq2SeqLM.from_pretrained(model_name_finetuned
                                                      , local_files_only=True)
        translated = model.generate(**tokenizer(src_text, return_tensors="pt", padding=True))
        translated = [tokenizer.decode(t, skip_special_tokens=True) for t in translated]
        return translated[0]

    # My name is Sarah and I live in London
    def score(self):
        """
        Function to calculate model metrics according to the evaluation dataset
        """
        metrics = self.trainer.evaluate()
        return metrics["eval_bleu"] / 100

    def get_params(self):
        """
        Dummy function for the moment
        """
        params_dict = {
            "ngram_min_n": 1,
            "ngram_max_n": 2,
        }
        return params_dict
