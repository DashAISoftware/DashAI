"""Source-agnostic mixin for components that download external artifacts.

Each downloadable component owns a directory ``<COMPONENT_PATH>/<ClassName>`` and
is responsible for downloading its artifacts into that directory and removing
them from it. There is no shared cache; ``HFDownloadableMixin`` covers the common
HuggingFace case by downloading each repo into the component's own folder.
"""

import logging
import os
import pathlib
import shutil
from typing import Callable, List, Optional, Tuple, Union

from huggingface_hub import snapshot_download
from kink import di

logger = logging.getLogger(__name__)

# report(fraction, message): fraction in [0, 1] or None for indeterminate.
ProgressReporter = Callable[[Optional[float], Optional[str]], None]


def _components_root() -> pathlib.Path:
    """Return the base directory that holds one folder per component."""
    return pathlib.Path(di["config"]["COMPONENT_PATH"])


class DownloadableMixin:
    """Marks a component as requiring an explicit download.

    Subclasses implement ``is_downloaded`` and ``download`` for their own source
    and store artifacts under ``component_dir()``. ``delete`` defaults to removing
    that directory. See ``HFDownloadableMixin`` for the HuggingFace case.
    """

    REQUIRES_DOWNLOAD: bool = True
    DOWNLOAD_SIZE_BYTES: Optional[int] = None

    @classmethod
    def component_dir(cls) -> pathlib.Path:
        """Return this component's own storage directory.

        Returns
        -------
        pathlib.Path
            ``<COMPONENT_PATH>/<ClassName>``.
        """
        return _components_root() / cls.__name__

    @classmethod
    def is_downloaded(cls) -> bool:
        """Return whether the component's artifacts are present locally."""
        raise NotImplementedError

    @classmethod
    def download(cls, report: Optional[ProgressReporter] = None) -> None:
        """Fetch the component's artifacts into ``component_dir()``."""
        raise NotImplementedError

    @classmethod
    def delete(cls) -> None:
        """Remove the component's downloaded artifacts."""
        shutil.rmtree(cls.component_dir(), ignore_errors=True)


class HFDownloadableMixin(DownloadableMixin):
    """Downloadable component whose artifacts are HuggingFace repos.

    Each repo is downloaded into ``component_dir()/<repo-leaf>``. Subclasses set
    ``HF_REPOS`` or, for a dynamic repo (e.g. derived from a per-subclass
    ``MODEL_NAME``), override ``hf_repos``.

    ``HF_REPOS`` entries accept two shapes:

    * ``(repo_id, repo_type)`` -- full snapshot download (original behavior).
    * ``(repo_id, repo_type, allow_patterns)`` -- partial download; only files
      matching the glob patterns in ``allow_patterns`` are fetched.

    ``HF_IGNORE_PATTERNS`` is applied to every repo download to skip the
    non-PyTorch weight formats HuggingFace repos ship alongside the PyTorch /
    safetensors weights (TensorFlow, Flax, Rust, ONNX, OpenVINO, CoreML). These
    are never used by ``from_pretrained`` here, so dropping them shrinks the
    download without affecting fine-tuning or inference. It keeps both ``.bin``
    and ``.safetensors`` so any model still has a loadable weight.
    """

    HF_REPOS: List[Union[Tuple[str, str], Tuple[str, str, List[str]]]] = []
    #: Alternate-framework artifacts to skip on every download (``*`` matches
    #: path separators in ``huggingface_hub`` glob semantics, so these match at
    #: any depth, e.g. ``unet/diffusion_flax_model.msgpack``).
    HF_IGNORE_PATTERNS: Optional[List[str]] = [
        "*.h5",
        "*.msgpack",
        "*.ot",
        "*.onnx",
        "*.onnx_data",
        "*.tflite",
        "*.mlmodel",
        "*openvino*",
        "*coreml*",
    ]

    @classmethod
    def hf_repos(cls) -> List[Union[Tuple[str, str], Tuple[str, str, List[str]]]]:
        """Return the repo entries this component needs.

        Returns
        -------
        list of tuple
            Each entry is either ``(repo_id, repo_type)`` or
            ``(repo_id, repo_type, allow_patterns)``.
        """
        return list(cls.HF_REPOS)

    @classmethod
    def _unpack_entry(
        cls,
        entry: Union[Tuple[str, str], Tuple[str, str, List[str]]],
    ) -> Tuple[str, str, Optional[List[str]]]:
        """Normalise a repo entry into ``(repo_id, repo_type, allow_patterns)``.
        Parameters
        ----------
        entry : tuple
            Either a 2-tuple ``(repo_id, repo_type)`` or a 3-tuple
            ``(repo_id, repo_type, allow_patterns)``.

        Returns
        -------
        tuple of (str, str, list[str] or None)
            ``repo_id``, ``repo_type``, and ``allow_patterns`` (``None`` when
            the entry was a 2-tuple, meaning a full snapshot download).

        Raises
        ------
        ValueError
            If ``entry`` has a length other than 2 or 3.
        """
        if len(entry) == 2:
            rid, rtype = entry
            return rid, rtype, None
        if len(entry) == 3:
            rid, rtype, patterns = entry
            return rid, rtype, patterns
        raise ValueError(
            f"HF_REPOS entries must be 2- or 3-tuples; "
            f"got length {len(entry)}: {entry!r}"
        )

    @classmethod
    def _repo_dir(cls, repo_id: str) -> pathlib.Path:
        """Return the local directory for a single repo under component_dir().

        Parameters
        ----------
        repo_id : str
            HuggingFace repo identifier, e.g. ``"owner/model-name"``.

        Returns
        -------
        pathlib.Path
            ``component_dir()/<repo-leaf>``.
        """
        return cls.component_dir() / repo_id.split("/")[-1]

    @classmethod
    def is_downloaded(cls) -> bool:
        """Return whether all repo directories exist and are non-empty.

        Returns
        -------
        bool
            ``True`` when every repo listed in ``hf_repos()`` has a non-empty
            local directory; ``False`` otherwise (including when the list is
            empty).
        """
        repos = cls.hf_repos()
        return bool(repos) and all(
            cls._repo_dir(rid).is_dir() and any(cls._repo_dir(rid).iterdir())
            for rid, *_ in repos
        )

    @classmethod
    def _local_or_repo(cls, repo_id: str) -> str:
        """Return the local dir for a repo if downloaded, else the repo id.

        Lets multi-repo components (e.g. ControlNet pipelines) load each repo
        from the component's own download folder when present, falling back to
        the Hub otherwise. Downloading is enforced by the run/session gates.

        Parameters
        ----------
        repo_id : str
            HuggingFace repo identifier.

        Returns
        -------
        str
            A local path (when the repo is present) or ``repo_id``.
        """
        try:
            target = cls._repo_dir(repo_id)
            if target.is_dir() and any(target.iterdir()):
                return str(target)
        except Exception:
            pass
        return repo_id

    @classmethod
    def download(cls, report: Optional[ProgressReporter] = None) -> None:
        """Download all repos listed in ``hf_repos()`` into ``component_dir()``.

        Parameters
        ----------
        report : ProgressReporter, optional
            Callback invoked before each repo download with
            ``report(None, "Downloading <repo_id>")``.  ``None`` means no
            progress reporting.
        """
        # Force the classic HTTP/LFS transfer path. The Xet backend can return
        # a 404 on its read-token endpoint for some repos (e.g. bert-base-
        # uncased), which aborts the whole download; the classic path is
        # slower but reliable.
        os.environ["HF_HUB_DISABLE_XET"] = "1"
        try:
            from huggingface_hub import constants as hf_constants

            hf_constants.HF_HUB_DISABLE_XET = True
        except Exception:
            pass

        for entry in cls.hf_repos():
            rid, rtype, allow_patterns = cls._unpack_entry(entry)
            target = cls._repo_dir(rid)
            target.mkdir(parents=True, exist_ok=True)
            if report is not None:
                # snapshot_download exposes no aggregate byte count, so progress
                # is reported as indeterminate (None) with a phase message.
                report(None, f"Downloading {rid}")
            kwargs = {}
            if allow_patterns is not None:
                kwargs["allow_patterns"] = allow_patterns
            if cls.HF_IGNORE_PATTERNS:
                kwargs["ignore_patterns"] = list(cls.HF_IGNORE_PATTERNS)
            snapshot_download(
                repo_id=rid, repo_type=rtype, local_dir=str(target), **kwargs
            )


class HFPretrainedDownloadMixin(HFDownloadableMixin):
    """HuggingFace mixin for models built around a single ``MODEL_NAME`` repo.

    Covers the common ``from_pretrained`` case: the repo is derived from the
    subclass ``MODEL_NAME`` and ``_pretrained_source`` returns where to load
    from (a saved run, the local download folder, or the Hub as a fallback).
    """

    MODEL_NAME: str = ""

    @classmethod
    def hf_repos(cls):
        """Derive the single repo entry from ``MODEL_NAME``.

        Returns
        -------
        list of tuple of (str, str)
            ``[(MODEL_NAME, "model")]`` or an empty list when unset.
        """
        return [(cls.MODEL_NAME, "model")] if cls.MODEL_NAME else []

    def _pretrained_source(self, pretrained_dir: Optional[str] = None) -> str:
        """Resolve where ``from_pretrained`` should load from.

        Prefers an explicit ``pretrained_dir`` (a saved run), then the local
        component download folder when present, and finally falls back to the
        Hub repo id. Downloading is enforced by the run/session gates before
        real use; the Hub fallback keeps direct instantiation working when
        nothing has been downloaded.

        Parameters
        ----------
        pretrained_dir : str or None
            Directory of a previously saved run, if any.

        Returns
        -------
        str
            A path or repo id accepted by ``from_pretrained``.
        """
        if pretrained_dir:
            return pretrained_dir
        try:
            if self.is_downloaded():
                return str(self._repo_dir(self.MODEL_NAME))
        except Exception:
            pass
        return self.MODEL_NAME


class TorchvisionDownloadMixin(DownloadableMixin):
    """Downloadable mixin for torchvision models with ImageNet-pretrained weights.

    torchvision fetches pretrained weights into a global ``torch.hub`` cache.
    This mixin redirects that cache to ``component_dir()`` so the weights are
    stored and gated like any other downloadable component. Subclasses build
    their backbone inside :meth:`local_hub` so the pretrained weights are read
    from (and written to) the component's own folder.

    .. note::
        The download provides the ImageNet weights used when the model is built
        with ``pretrained=True`` (the default). Training a fresh model with
        ``pretrained=False`` needs no weights but is still gated as a
        download-required component.
    """

    @classmethod
    def _weights(cls):
        """Return the torchvision weights enum member to download.

        Returns
        -------
        torchvision.models.WeightsEnum
            The pretrained weights descriptor whose file is fetched.
        """
        raise NotImplementedError

    @classmethod
    def _checkpoints_dir(cls):
        """Return the directory where torch.hub stores downloaded checkpoints."""
        return cls.component_dir() / "checkpoints"

    @classmethod
    def local_hub(cls):
        """Context manager that points ``torch.hub`` at ``component_dir()``.

        Returns
        -------
        contextlib.AbstractContextManager
            A context that temporarily sets the torch hub directory to this
            component's folder and restores the previous value on exit.
        """
        import contextlib

        import torch

        @contextlib.contextmanager
        def _ctx():
            old = torch.hub.get_dir()
            cls.component_dir().mkdir(parents=True, exist_ok=True)
            torch.hub.set_dir(str(cls.component_dir()))
            try:
                yield
            finally:
                torch.hub.set_dir(old)

        return _ctx()

    @classmethod
    def is_downloaded(cls) -> bool:
        """Return whether the pretrained weights file is present locally.

        Returns
        -------
        bool
            ``True`` when the component's ``checkpoints`` folder exists and is
            non-empty.
        """
        ckpt = cls._checkpoints_dir()
        return ckpt.is_dir() and any(ckpt.iterdir())

    @classmethod
    def download(cls, report: Optional[ProgressReporter] = None) -> None:
        """Fetch the pretrained weights into ``component_dir()``.

        Parameters
        ----------
        report : ProgressReporter, optional
            Callback invoked with an indeterminate progress message.
        """
        if report is not None:
            report(None, f"Downloading {cls.__name__} weights")
        with cls.local_hub():
            cls._weights().get_state_dict(progress=False)
