from typing import Dict

from DashAI.back.models.RAG.embeddings.dense._overflow_handler import (
    OverflowHandler,
)

CLS = "cls"
MEAN = "mean"
MAX = "max"
CONCAT_2 = "concat_2"
CONCAT_3 = "concat_3"
CONCAT_4 = "concat_4"

POOLING_STRATEGIES: Dict[str, str] = {
    CLS: "CLS token",
    MEAN: "Mean pooling",
    MAX: "Max pooling",
    CONCAT_2: "Concat last 2 layers",
    CONCAT_3: "Concat last 3 layers",
    CONCAT_4: "Concat last 4 layers",
}


class _BERTEmbedding(OverflowHandler):
    """Internal wrapper for BERT-family embedding models.

    Supports multiple pooling strategies: CLS token, mean, max, and
    concatenation of the last N hidden layers.
    """

    POOLING_STRATEGIES: Dict[str, str] = POOLING_STRATEGIES

    def __init__(
        self,
        model_name: str,
        device: str,
        model_max_length: int,
        overflow_strategy: str,
        pooling_strategy: str,
    ):
        """Initialise the BERT embedding wrapper.

        Args:
            model_name: HuggingFace model identifier.
            device: Target device (``"cpu"`` or ``"cuda"``).
            model_max_length: Maximum token length.
            overflow_strategy: ``"truncate"`` or ``"aggregate"``.
            pooling_strategy: One of ``"cls"``, ``"mean"``, ``"max"``,
                ``"concat_2"``, ``"concat_3"``, ``"concat_4"``.
        """
        super().__init__(
            model_name=model_name,
            device=device,
            model_max_length=model_max_length,
            overflow_strategy=overflow_strategy,
        )
        self.pooling_strategy = pooling_strategy
        self.params["pooling_strategy"] = pooling_strategy

    def load(self):
        """Download tokenizer and model, enabling hidden states for concat strategies."""  # noqa: E501
        from transformers import AutoModel, AutoTokenizer

        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.model = AutoModel.from_pretrained(
            self.model_name,
            output_hidden_states=self.pooling_strategy
            in (CONCAT_2, CONCAT_3, CONCAT_4),
        ).to(self.device)

    def _pool(self, model_output, attention_mask):
        """Pool token embeddings according to the configured strategy.

        Args:
            model_output: Output from ``AutoModel`` (may contain ``hidden_states``).
            attention_mask: Attention mask tensor.

        Returns:
            Pooled embedding tensor of shape ``(batch, embedding_dim)``.

        Raises:
            ValueError: If the pooling strategy is unknown.
        """
        import torch

        if self.pooling_strategy == CLS:
            return model_output[0][:, 0]
        if self.pooling_strategy == MAX:
            token_embeddings = model_output[0]
            input_mask_expanded = (
                attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
            )
            token_embeddings[input_mask_expanded == 0] = -1e9
            return torch.max(token_embeddings, 1)[0]
        if self.pooling_strategy in (CONCAT_2, CONCAT_3, CONCAT_4):
            hidden_states = model_output.hidden_states
            layer_count = int(self.pooling_strategy.split("_")[1])
            selected = [hidden_states[-(i + 1)][:, 0, :] for i in range(layer_count)]
            return torch.cat(selected, dim=1)
        token_embeddings = model_output[0]
        input_mask_expanded = (
            attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
        )
        pooled = torch.sum(token_embeddings * input_mask_expanded, 1) / torch.clamp(
            input_mask_expanded.sum(1), min=1e-9
        )
        return pooled
