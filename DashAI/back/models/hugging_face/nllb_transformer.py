"""NLLB transformer model for multilingual translation DashAI implementation."""

import shutil
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING, List, Optional, Union

from sklearn.exceptions import NotFittedError

from DashAI.back.core.schema_fields import schema_field, string_field
from DashAI.back.core.utils import MultilingualString
from DashAI.back.dependencies.downloads.downloadable import (
    HFPretrainedDownloadMixin,
)
from DashAI.back.models.hugging_face.opus_mt_en_es_transformer import (
    OpusMtEnESTransformerSchema,
)
from DashAI.back.models.translation_model import TranslationModel
from DashAI.back.models.utils import (
    GPU_OR_CPU_PLACEHOLDER,
    resolve_temp_checkpoint_dir,
)

if TYPE_CHECKING:
    from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset


class NllbTransformerSchema(OpusMtEnESTransformerSchema):
    """Schema for the NLLB multilingual translation model. Extends the standard
    translation schema with ``source_language`` and ``target_language`` fields,
    which accept NLLB language codes in the form ``<iso639>_<script>``
    (e.g. ``spa_Latn`` for Spanish, ``eng_Latn`` for English).
    """

    source_language: schema_field(
        string_field(),
        placeholder="spa_Latn",
        description=MultilingualString(
            en=(
                "Source language code for NLLB tokenizer (e.g. spa_Latn for Spanish, "
                "eng_Latn for English). It uses BCP-47 language tags in the format"
                "[Examples](https://dl-translate.readthedocs.io/en/latest/available_lang"
                "uages/#nllb-200)"
            ),
            es=(
                "Código de idioma de origen para el tokenizer NLLB (ej. spa_Latn para "
                "español, eng_Latn para inglés). Utiliza etiquetas de idioma BCP-47 "
                "en el formato "
                "[Ejemplos](https://dl-translate.readthedocs.io/en/latest/available_lang"
                "uages/#nllb-200)"
            ),
            pt=(
                "Código do idioma de origem para o tokenizer NLLB (ex. spa_Latn para "
                "espanhol, eng_Latn para inglês). Utiliza tags de idioma BCP-47 "
                "no formato "
                "[Exemplos](https://dl-translate.readthedocs.io/en/latest/available_lang"
                "uages/#nllb-200)"
            ),
            de=(
                "Quellsprachcode für den NLLB-Tokenisierer (z.B. spa_Latn für Spanisch,"
                "eng_Latn für Englisch). Verwendet BCP-47-Sprach-Tags im Format "
                "[Beispiele](https://dl-translate.readthedocs.io/en/latest/available_lan"
                "guages/#nllb-200)"
            ),
            zh=(
                "NLLB 分词器的源语言代码（例如 spa_Latn 表示西班牙语，"
                "eng_Latn 表示英语）。使用 BCP-47 语言标签格式 "
                "[示例](https://dl-translate.readthedocs.io/en/latest/available_lang"
                "uages/#nllb-200)"
            ),
        ),
        alias=MultilingualString(
            en="Source language",
            es="Idioma de origen",
            pt="Idioma de origem",
            de="Quellsprache",
            zh="源语言",
        ),
    )  # type: ignore
    target_language: schema_field(
        string_field(),
        placeholder="eng_Latn",
        description=MultilingualString(
            en=(
                "Target language code for NLLB generation (e.g. eng_Latn for English, "
                "fra_Latn for French). It uses BCP-47 language tags in the format "
                "[Examples](https://dl-translate.readthedocs.io/en/latest/available_lang"
                "uages/#nllb-200)"
            ),
            es=(
                "Código de idioma destino para la generación NLLB (ej. eng_Latn para "
                "inglés, fra_Latn para francés). Utiliza etiquetas de idioma BCP-47 "
                "en el formato "
                "[Ejemplos](https://dl-translate.readthedocs.io/en/latest/available_lang"
                "uages/#nllb-200)"
            ),
            pt=(
                "Código do idioma de destino para a geração NLLB (ex. eng_Latn para "
                "inglês, fra_Latn para francês). Utiliza tags de idioma BCP-47 "
                "no formato "
                "[Exemplos](https://dl-translate.readthedocs.io/en/latest/available_lang"
                "uages/#nllb-200)"
            ),
            de=(
                "Zielsprachcode für die NLLB-Erzeugung (z.B. eng_Latn für Englisch, "
                "fra_Latn für Französisch). Verwendet BCP-47-Sprach-Tags im Format "
                "[Beispiele](https://dl-translate.readthedocs.io/en/latest/available_lan"
                "guages/#nllb-200)"
            ),
            zh=(
                "NLLB 生成的目标语言代码（例如 eng_Latn 表示英语，"
                "fra_Latn 表示法语）。使用 BCP-47 语言标签格式 "
                "[示例](https://dl-translate.readthedocs.io/en/latest/available_lang"
                "uages/#nllb-200)"
            ),
        ),
        alias=MultilingualString(
            en="Target language",
            es="Idioma destino",
            pt="Idioma de destino",
            de="Zielsprache",
            zh="目标语言",
        ),
    )  # type: ignore


class NllbTransformer(HFPretrainedDownloadMixin, TranslationModel):
    """Pretrained transformer for configurable multilingual translation.

    This model fine-tunes the ``facebook/nllb-200-distilled-600M`` checkpoint from
    Meta AI's No Language Left Behind (NLLB) project. The base model supports
    translation across 200 languages using a single unified model, identified by
    NLLB language codes of the form ``<iso639>_<script>`` (e.g. ``spa_Latn``,
    ``eng_Latn``). The 600M parameter distilled variant provides a balance between
    translation quality and computational cost.

    Target language generation is guided by ``forced_bos_token_id``, which forces
    the decoder to start with the target language token. Fine-tuning is performed
    with the HuggingFace ``Seq2SeqTrainer`` using the AdamW optimizer. Training and
    validation metrics are logged at configurable epoch and step intervals via a
    custom ``MetricsCallback``.

    References
    ----------
    - [1] https://huggingface.co/facebook/nllb-200-distilled-600M
    - [2] https://arxiv.org/abs/2207.04672
    """

    SCHEMA = NllbTransformerSchema
    DISPLAY_NAME: str = MultilingualString(
        en="NLLB Transformer",
        es="Transformer NLLB",
        pt="Transformer NLLB",
        de="NLLB Transformer",
        zh="NLLB Transformer",
    )
    DESCRIPTION: str = MultilingualString(
        en=("NLLB multilingual model for configurable source to target translation."),
        es=("Modelo multilenguaje NLLB para traduccion configurable origen-destino."),
        pt=("Modelo multilingual NLLB para tradução configurável origem-destino."),
        de=("Mehrsprachiges NLLB-Modell für konfigurierbare Quell-Ziel-Übersetzung."),
        zh="NLLB 多语言模型，支持可配置的源语言到目标语言翻译。",
    )
    COLOR: str = "#5E35B1"
    ICON: str = "Translate"

    def _resolve_language_token_id(self, language_code: str, field_name: str) -> int:
        """Resolve an NLLB language code to its vocabulary token ID.

        Tries ``tokenizer.lang_code_to_id`` first (available on
        ``NllbTokenizer``), then falls back to ``convert_tokens_to_ids``.
        Raises ``ValueError`` when the code is not found in either lookup.

        Parameters
        ----------
        language_code : str
            NLLB language code in ``<iso639>_<script>`` format
            (e.g. ``spa_Latn``, ``eng_Latn``).
        field_name : str
            Name of the field being resolved, used in the error message
            (e.g. ``"source_language"``).

        Returns
        -------
        int
            Token ID corresponding to ``language_code`` in the tokenizer
            vocabulary.

        Raises
        ------
        ValueError
            If ``language_code`` cannot be resolved by either lookup method.
        """
        lang_code_to_id = getattr(self.tokenizer, "lang_code_to_id", None)
        if isinstance(lang_code_to_id, dict) and language_code in lang_code_to_id:
            return lang_code_to_id[language_code]

        convert_tokens_to_ids = getattr(self.tokenizer, "convert_tokens_to_ids", None)
        if callable(convert_tokens_to_ids):
            token_id = convert_tokens_to_ids(language_code)
            unk_token_id = getattr(self.tokenizer, "unk_token_id", None)
            if token_id not in {None, -1, unk_token_id}:
                return token_id

        raise ValueError(f"Unsupported {field_name} '{language_code}'.")

    MODEL_NAME: str = "facebook/nllb-200-distilled-600M"
    DOWNLOAD_SIZE_BYTES: int = 2482655255

    def __init__(self, model=None, pretrained_dir=None, **kwargs):
        """Initialize the NLLB tokenizer and model.

        Downloads the ``facebook/nllb-200-distilled-600M`` tokenizer and,
        when ``model`` is ``None``, the seq2seq model weights from HuggingFace.
        Resolves the source and target language codes to vocabulary token IDs
        and sets ``tokenizer.src_lang`` when the attribute is available.

        Parameters
        ----------
        model : transformers.PreTrainedModel or None, optional
            An already loaded HuggingFace seq2seq model to reuse. If ``None``,
            the ``facebook/nllb-200-distilled-600M`` checkpoint is downloaded
            and initialised. Default ``None``.
        **kwargs : dict
            Hyperparameters forwarded to ``validate_and_transform`` and used to
            configure training (e.g. ``num_train_epochs``, ``batch_size``,
            ``learning_rate``, ``weight_decay``, ``device``,
            ``source_language``, ``target_language``).

        Raises
        ------
        ValueError
            If ``source_language`` or ``target_language`` cannot be resolved to
            a token ID in the tokenizer vocabulary.
        """
        kwargs = self.validate_and_transform(kwargs)

        from transformers import AutoTokenizer

        self.model_name = self._pretrained_source(pretrained_dir)
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)

        self.source_language = kwargs.get("source_language", "spa_Latn")
        self.target_language = kwargs.get("target_language", "eng_Latn")

        self.source_language_token_id = self._resolve_language_token_id(
            self.source_language,
            "source_language",
        )
        self.target_language_token_id = self._resolve_language_token_id(
            self.target_language,
            "target_language",
        )

        if hasattr(self.tokenizer, "src_lang"):
            self.tokenizer.src_lang = self.source_language

        self.training_args = {
            "num_train_epochs": kwargs.get("num_train_epochs", 2),
            "learning_rate": kwargs.get("learning_rate", 2e-5),
            "weight_decay": kwargs.get("weight_decay", 0.01),
        }
        self.batch_size = kwargs.get("batch_size", 4)
        self.device = kwargs.get("device") or GPU_OR_CPU_PLACEHOLDER
        self.log_train_every_n_epochs = kwargs.get("log_train_every_n_epochs", 1)
        self.log_train_every_n_steps = kwargs.get("log_train_every_n_steps", None)
        self.log_validation_every_n_epochs = kwargs.get(
            "log_validation_every_n_epochs", 1
        )
        self.log_validation_every_n_steps = kwargs.get(
            "log_validation_every_n_steps", None
        )

        if model is None:
            from transformers import AutoModelForSeq2SeqLM

            self.model = AutoModelForSeq2SeqLM.from_pretrained(self.model_name)
        else:
            self.model = model

        self.num_train_epochs = self.training_args.get("num_train_epochs", 2)
        self.fitted = model is not None

    def tokenize_data(
        self, x: "DashAIDataset", y: Optional["DashAIDataset"] = None
    ) -> "DashAIDataset":
        """Tokenize input and optional target datasets for seq2seq training.

        Sets ``tokenizer.src_lang`` to ``source_language`` before tokenizing
        so the NLLB tokenizer inserts the correct language prefix token. Each
        sample is tokenized with truncation and max length padding to 512
        tokens. When ``y`` is provided, target tokens are stored under the
        ``labels`` key.

        Parameters
        ----------
        x : DashAIDataset
            Source language dataset. Only the first column is used.
        y : DashAIDataset, optional
            Target language dataset. When provided, tokenized targets are added
            as ``labels``. When ``None``, only ``input_ids`` and
            ``attention_mask`` are returned (inference mode).

        Returns
        -------
        DashAIDataset
            Tokenized dataset with keys ``input_ids``, ``attention_mask``, and
            optionally ``labels``.
        """
        from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset

        if hasattr(self.tokenizer, "src_lang"):
            self.tokenizer.src_lang = self.source_language

        is_y = bool(y)
        if not y:
            y = DashAIDataset.from_list([{"foo": 0}] * len(x))

        dataset = []
        input_column_name = x.column_names[0]
        output_column_name = y.column_names[0] if is_y else None

        for i, input_sample in enumerate(x):
            tokenized_input = self.tokenizer(
                input_sample[input_column_name],
                truncation=True,
                padding="max_length",
                max_length=512,
            )

            sample = {
                "input_ids": tokenized_input["input_ids"],
                "attention_mask": tokenized_input["attention_mask"],
            }

            if is_y:
                output_sample = y[i]
                tokenized_output = self.tokenizer(
                    output_sample[output_column_name],
                    truncation=True,
                    padding="max_length",
                    max_length=512,
                )
                sample["labels"] = tokenized_output["input_ids"]

            dataset.append(sample)

        return DashAIDataset.from_list(dataset)

    def train(
        self,
        x_train: "DashAIDataset",
        y_train: "DashAIDataset",
        x_validation: "DashAIDataset" = None,
        y_validation: "DashAIDataset" = None,
    ) -> "NllbTransformer":
        """Fine-tune the NLLB model on the configured language pair.

        Parameters
        ----------
        x_train : DashAIDataset
            Input source language text features for training.
        y_train : DashAIDataset
            Target language translation labels for training.
        x_validation : DashAIDataset, optional
            Input source language text features for validation. Default
            ``None``.
        y_validation : DashAIDataset, optional
            Target language translation labels for validation. Default ``None``.

        Returns
        -------
        NllbTransformer
            The fine-tuned model instance.
        """
        from transformers import Seq2SeqTrainer, Seq2SeqTrainingArguments

        from DashAI.back.models.hugging_face.metrics_callback import MetricsCallback

        dataset = self.tokenize_data(x_train, y_train)
        dataset.set_format("torch", columns=["input_ids", "attention_mask", "labels"])

        has_validation_data = x_validation is not None and y_validation is not None

        output_root = resolve_temp_checkpoint_dir(
            "DashAI/back/user_models/temp_checkpoints_nllb"
        )
        output_root.mkdir(parents=True, exist_ok=True)
        run_output_dir = tempfile.mkdtemp(prefix="nllb_", dir=str(output_root))

        training_args = Seq2SeqTrainingArguments(
            output_dir=run_output_dir,
            save_steps=1,
            save_total_limit=1,
            per_device_train_batch_size=self.batch_size,
            per_device_eval_batch_size=self.batch_size,
            use_cpu=self.device.lower() != "gpu",
            **self.training_args,
        )

        metrics_callback = MetricsCallback(
            model_instance=self,
            x_train=x_train,
            y_train=y_train,
            x_val=x_validation,
            y_val=y_validation,
            total_epochs=self.num_train_epochs,
            log_training_every_n_epochs=self.log_train_every_n_epochs,
            log_training_every_n_steps=self.log_train_every_n_steps,
            log_val_every_n_epochs=(
                self.log_validation_every_n_epochs if has_validation_data else None
            ),
            log_val_every_n_steps=(
                self.log_validation_every_n_steps if has_validation_data else None
            ),
        )

        trainer = Seq2SeqTrainer(
            model=self.model,
            args=training_args,
            train_dataset=dataset,
            callbacks=[metrics_callback],
        )

        self.fitted = True
        try:
            trainer.train()
        finally:
            shutil.rmtree(run_output_dir, ignore_errors=True)

        return self

    def predict(self, x_pred: "DashAIDataset") -> List:
        """Translate source texts to the configured target language.

        Uses ``forced_bos_token_id`` to force the decoder to start with the
        target language token, ensuring NLLB generates output in the correct
        language.

        Parameters
        ----------
        x_pred : DashAIDataset
            Source language dataset. Only the first column is used.

        Returns
        -------
        list of str
            One translated string per input sample, in the same order as
            ``x_pred``.

        Raises
        ------
        sklearn.exceptions.NotFittedError
            If the model has not been fine-tuned yet (``fitted`` is ``False``).
        """
        if not self.fitted:
            raise NotFittedError(
                f"This {self.__class__.__name__} instance is not fitted yet. Call 'fit'"
                " with appropriate arguments before using this estimator."
            )

        import torch

        if self.device.lower() == "gpu" and torch.cuda.is_available():
            self.model.to("cuda")
        else:
            self.model.to("cpu")
        self.model.eval()

        if self.device.lower() == "gpu":
            self.model.to("cuda")
        else:
            self.model.to("cpu")
        self.model.eval()

        dataset = self.tokenize_data(x_pred)
        dataset.set_format(type="torch", columns=["input_ids", "attention_mask"])

        translations = []
        target_bos = self.target_language_token_id

        for example in dataset:
            inputs = {
                k: v.unsqueeze(0).to(self.model.device) for k, v in example.items()
            }
            outputs = self.model.generate(
                **inputs,
                forced_bos_token_id=target_bos,
            )
            translated_text = self.tokenizer.decode(
                outputs[0], skip_special_tokens=True
            )
            translations.append(translated_text)

        return translations

    def prepare_dataset(
        self, dataset: "DashAIDataset", is_fit: bool = False
    ) -> "DashAIDataset":
        """Return the dataset unchanged.

        No preprocessing transformations are required for this model. The
        method exists for compatibility with the DashAI model interface.

        Parameters
        ----------
        dataset : DashAIDataset
            The dataset to be prepared.
        is_fit : bool, optional
            Whether the call is made during fitting. Unused here. Default
            ``False``.

        Returns
        -------
        DashAIDataset
            The original dataset, unmodified.
        """
        return dataset

    def save(self, filename: Union[str, "Path"]) -> None:
        """Store the fine-tuned model and its configuration to disk.

        Saves the model weights via ``save_pretrained`` and embeds the
        hyperparameters (epochs, batch size, learning rate, language codes,
        etc.) into the HuggingFace config so they can be restored by
        :meth:`load`.

        Parameters
        ----------
        filename : str or Path
            Directory path where the model files will be written. If a file
            exists at that path it is removed and replaced by a directory.
        """
        from transformers import AutoConfig

        save_dir = Path(filename)
        if save_dir.exists() and save_dir.is_file():
            save_dir.unlink()
        save_dir.mkdir(parents=True, exist_ok=True)

        self.model.save_pretrained(save_dir)
        self.tokenizer.save_pretrained(save_dir)
        config = AutoConfig.from_pretrained(save_dir)
        config.custom_params = {
            "num_train_epochs": self.training_args.get("num_train_epochs"),
            "batch_size": self.batch_size,
            "learning_rate": self.training_args.get("learning_rate"),
            "device": self.device,
            "weight_decay": self.training_args.get("weight_decay"),
            "source_language": self.source_language,
            "target_language": self.target_language,
            "fitted": self.fitted,
        }
        config.save_pretrained(save_dir)

    @classmethod
    def load(cls, filename: Union[str, "Path"]):
        """Restore an NllbTransformer instance from disk.

        Reads the HuggingFace config to recover the custom hyperparameters
        saved by :meth:`save`, then reconstructs the seq2seq model and wraps
        it in a new :class:`NllbTransformer` instance.

        Parameters
        ----------
        filename : str or Path
            Directory path from which the model files will be read.

        Returns
        -------
        NllbTransformer
            The restored model instance with ``fitted`` set to the persisted
            value.
        """
        from transformers import AutoConfig, AutoModelForSeq2SeqLM

        model = AutoModelForSeq2SeqLM.from_pretrained(filename)
        config = AutoConfig.from_pretrained(filename)
        custom_params = getattr(config, "custom_params", {})

        loaded_model = cls(
            model=model,
            pretrained_dir=str(filename),
            num_train_epochs=custom_params.get("num_train_epochs"),
            batch_size=custom_params.get("batch_size"),
            learning_rate=custom_params.get("learning_rate"),
            device=custom_params.get("device"),
            weight_decay=custom_params.get("weight_decay"),
            source_language=custom_params.get("source_language", "spa_Latn"),
            target_language=custom_params.get("target_language", "eng_Latn"),
            log_train_every_n_epochs=None,
            log_train_every_n_steps=None,
            log_validation_every_n_epochs=None,
            log_validation_every_n_steps=None,
        )
        loaded_model.fitted = custom_params.get("fitted", False)
        return loaded_model
