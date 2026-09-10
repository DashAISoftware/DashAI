from transformers import TrainerCallback

from DashAI.back.core.enums.metrics import LevelEnum, SplitEnum


class MetricsCallback(TrainerCallback):
    """HuggingFace Trainer callback that persists DashAI metrics during training.

    Hooks into the HuggingFace ``Trainer`` lifecycle to calculate and store
    per-epoch and per-step metrics for both training and validation splits.
    Metrics are written to the DashAI database via ``model_instance.calculate_metrics``.
    """

    def __init__(
        self,
        model_instance,
        x_train,
        y_train,
        total_epochs,
        x_val=None,
        y_val=None,
        log_training_every_n_epochs=1,
        log_training_every_n_steps=50,
        log_val_every_n_epochs=1,
        log_val_every_n_steps=50,
    ):
        """Initialize the callback with data and logging frequency settings.

        Parameters
        ----------
        model_instance : BaseModel
            The DashAI model instance whose ``calculate_metrics`` method will be
            called to persist computed scores.
        x_train : DashAIDataset or array-like
            Training input features. Converted to ``DashAIDataset`` on init.
        y_train : DashAIDataset or array-like
            Training target labels. Converted to ``DashAIDataset`` on init.
        x_val : DashAIDataset or array-like
            Validation input features. Converted to ``DashAIDataset`` on init.
        y_val : DashAIDataset or array-like
            Validation target labels. Converted to ``DashAIDataset`` on init.
        total_epochs : int
            Total number of training epochs (stored for reference).
        log_training_every_n_epochs : int, optional
            Log training metrics every N completed epochs. Defaults to 1.
        log_training_every_n_steps : int, optional
            Log training metrics every N optimizer steps. Defaults to 50.
        log_val_every_n_epochs : int, optional
            Log validation metrics every N completed epochs. Defaults to 1.
        log_val_every_n_steps : int, optional
            Log validation metrics every N optimizer steps. Defaults to 50.
        """
        from DashAI.back.dataloaders.classes.dashai_dataset import to_dashai_dataset

        self.model_instance = model_instance
        self.x_train = to_dashai_dataset(x_train)
        self.y_train = to_dashai_dataset(y_train)
        self.x_val = to_dashai_dataset(x_val) if x_val is not None else None
        self.y_val = to_dashai_dataset(y_val) if y_val is not None else None
        self.log_training_every_n_epochs = log_training_every_n_epochs
        self.log_training_every_n_steps = log_training_every_n_steps
        self.log_val_every_n_epochs = log_val_every_n_epochs
        self.log_val_every_n_steps = log_val_every_n_steps
        self.total_epochs = total_epochs
        self.current_step = 0
        self.last_logged_epoch = 0  # Track last logged epoch to prevent duplicates

    def on_epoch_end(self, args, state, control, **kwargs):
        """Log metrics at the end of each training epoch.

        Called by the HuggingFace Trainer after every epoch. Skips duplicate
        epoch logging and respects the ``log_*_every_n_epochs`` frequency settings.

        Parameters
        ----------
        args : transformers.TrainingArguments
            Training configuration (unused directly).
        state : transformers.TrainerState
            Current trainer state; ``state.epoch`` provides the epoch counter.
        control : transformers.TrainerControl
            Object to signal training control flow changes (unused).
        **kwargs
            Additional keyword arguments passed by the Trainer (unused).
        """
        current_epoch = int(state.epoch)  # Use state.epoch from Trainer

        # Only log if we haven't already logged this epoch
        if current_epoch > self.last_logged_epoch:
            self.last_logged_epoch = current_epoch

            if (
                self.log_training_every_n_epochs
                and current_epoch % self.log_training_every_n_epochs == 0
            ):
                self.model_instance.calculate_metrics(
                    split=SplitEnum.TRAIN,
                    level=LevelEnum.EPOCH,
                    x_data=self.x_train,
                    y_data=self.y_train,
                    log_index=current_epoch,
                )

            if (
                self.log_val_every_n_epochs
                and self.x_val is not None
                and self.y_val is not None
                and current_epoch % self.log_val_every_n_epochs == 0
            ):
                self.model_instance.calculate_metrics(
                    split=SplitEnum.VALIDATION,
                    level=LevelEnum.EPOCH,
                    x_data=self.x_val,
                    y_data=self.y_val,
                    log_index=current_epoch,
                )

    def on_step_end(self, args, state, control, **kwargs):
        """Log metrics at the end of each optimizer step.

        Called by the HuggingFace Trainer after every gradient update step.
        Respects the ``log_*_every_n_steps`` frequency settings.

        Parameters
        ----------
        args : transformers.TrainingArguments
            Training configuration (unused directly).
        state : transformers.TrainerState
            Current trainer state (unused directly).
        control : transformers.TrainerControl
            Object to signal training control flow changes (unused).
        **kwargs
            Additional keyword arguments passed by the Trainer (unused).
        """
        self.current_step += 1

        if (
            self.log_training_every_n_steps
            and self.current_step % self.log_training_every_n_steps == 0
        ):
            self.model_instance.calculate_metrics(
                split=SplitEnum.TRAIN,
                level=LevelEnum.STEP,
                x_data=self.x_train,
                y_data=self.y_train,
                log_index=self.current_step,
            )

        if (
            self.log_val_every_n_steps
            and self.x_val is not None
            and self.y_val is not None
            and self.current_step % self.log_val_every_n_steps == 0
        ):
            self.model_instance.calculate_metrics(
                split=SplitEnum.VALIDATION,
                level=LevelEnum.STEP,
                x_data=self.x_val,
                y_data=self.y_val,
                log_index=self.current_step,
            )
