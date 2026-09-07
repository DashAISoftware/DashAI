import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from sqlalchemy import exc, select
from sqlalchemy.orm import Session

from DashAI.back.dependencies.database.models import (
    GenerativeSession,
    GenerativeSessionParameterHistory,
    RAGPrompt,
)
from DashAI.back.dependencies.registry.component_registry import ComponentRegistry
from DashAI.back.models.RAG.prompts.generation.default_QA_RAG_generation_prompt import (
    DefaultQARAGGenerationPrompt,
)
from DashAI.back.models.RAG.prompts.generation.default_RAG_generation_prompt import (
    DefaultRAGGenerationPrompt,
)
from DashAI.back.models.RAG.prompts.prompt import Prompt
from DashAI.back.services.RAG.exceptions import (
    RAGDatabaseError,
    RAGPromptValidationError,
)
from DashAI.back.services.RAG.utils import (
    build_parameters_hash,
    normalize_params,
)

log = logging.getLogger(__name__)


@dataclass
class PromptResponse:
    id: int
    class_name: str
    name: str | None
    parameters: dict[str, Any] | None
    created: datetime
    last_modified: datetime


class PromptService:
    """Service layer for RAG prompt CRUD, validation, and session-scoped copies."""

    def __init__(self, db: Session, registry: ComponentRegistry):
        self.db = db
        self._registry = registry

    def create(
        self, class_name: str, name: str, parameters: dict[str, Any]
    ) -> PromptResponse:
        """Create a RAGPrompt record.

        Validates templates via ``_validate_prompt_template()``, inserts the
        DB record, and returns the serialized prompt response.

        Args:
            class_name: Registered prompt component name.
            name: Human-readable name for the prompt.
            parameters: Prompt configuration including ``template`` or
                ``templates``.

        Returns:
            The newly created prompt response.

        Raises:
            RAGPromptValidationError: If validation fails.
            RAGDatabaseError: If a database error occurs.
        """
        if class_name not in self._registry:
            raise RAGPromptValidationError(
                f"Component {class_name} is not registered in the registry."
            )
        prompt_class = self._registry[class_name]["class"]
        if not issubclass(prompt_class, Prompt):
            raise RAGPromptValidationError(
                f"Component {class_name} is not a valid Prompt subclass."
            )

        if "templates" in parameters:
            for _lang, tmpl in parameters["templates"].items():
                self._validate_prompt_template(class_name, tmpl)
        elif "template" in parameters:
            self._validate_prompt_template(class_name, parameters["template"])
        else:
            raise RAGPromptValidationError(
                "Prompt parameters must include 'template' or 'templates'."
            )

        parameters = normalize_params(parameters)
        params_hash = build_parameters_hash(parameters)

        try:
            prompt = RAGPrompt(
                class_name=class_name,
                name=name,
                parameters=parameters,
                parameters_hash=params_hash,
            )
            self.db.add(prompt)
            self.db.commit()
            self.db.refresh(prompt)
            return self._serialize_prompt(prompt)
        except exc.SQLAlchemyError as e:
            self.db.rollback()
            log.exception(e)
            raise RAGDatabaseError("Error creating prompt in database.") from e

    def get_or_create(
        self, class_name: str, name: str, parameters: dict[str, Any]
    ) -> PromptResponse:
        """Lookup-or-create a RAGPrompt record.

        Searches for an existing prompt with the same class name and
        parameters and reuses it when found; otherwise inserts a new record.
        Unlike :meth:`create`, this does not enforce template presence so
        repeated pipeline builds can share a single prompt record.

        The lookup checks both the raw parameters and the sorted variant
        because rows created via :meth:`create` may store keys in a
        non-deterministic order (the UNIQUE constraint compares the
        serialized JSON text). Inserts always use the sorted variant so
        subsequent lookups are deterministic.

        Args:
            class_name: Registered prompt component name.
            name: Human-readable name for the prompt.
            parameters: Prompt configuration including ``template`` or
                ``templates``.

        Returns:
            The existing or newly created prompt response.

        Raises:
            RAGDatabaseError: If a database error occurs.
        """
        normalized = normalize_params(parameters)

        existing = self._find_by_hash(parameters)
        if existing is None and normalized != parameters:
            existing = self._find_by_hash(normalized)

        if existing is not None:
            return self._serialize_prompt(existing)

        params_hash = build_parameters_hash(normalized)
        try:
            prompt = RAGPrompt(
                class_name=class_name,
                name=name,
                parameters=normalized,
                parameters_hash=params_hash,
            )
            self.db.add(prompt)
            self.db.commit()
            self.db.refresh(prompt)
            return self._serialize_prompt(prompt)
        except exc.IntegrityError:
            self.db.rollback()
            existing = self._find_by_hash(parameters)
            if existing is None and normalized != parameters:
                existing = self._find_by_hash(normalized)
            if existing is not None:
                return self._serialize_prompt(existing)
            raise
        except exc.SQLAlchemyError as e:
            self.db.rollback()
            log.exception(e)
            raise RAGDatabaseError("Error creating prompt in database.") from e

    def _find_by_hash(self, params: dict[str, Any]) -> RAGPrompt | None:
        """Look up a prompt by its normalized parameters hash.

        Args:
            params: Parameters to compute hash from.

        Returns:
            Matching ``RAGPrompt`` or ``None``.

        Raises:
            RAGDatabaseError: On database error.
        """
        try:
            h = build_parameters_hash(params)
            return self.db.query(RAGPrompt).filter_by(parameters_hash=h).first()
        except exc.SQLAlchemyError as e:
            self.db.rollback()
            log.exception(e)
            raise RAGDatabaseError("Error looking up prompt by hash.") from e

    def update(
        self,
        prompt_id: int,
        name: str | None = None,
        parameters: dict[str, Any] | None = None,
    ) -> PromptResponse:
        """Update an existing prompt in place.

        Validates the template if parameters change.

        Args:
            prompt_id: Primary key of the prompt to update.
            name: New name (optional).
            parameters: New parameters including ``template`` or
                ``templates`` (optional).

        Returns:
            The updated prompt response.

        Raises:
            RAGPromptValidationError: If not found or validation fails.
            RAGDatabaseError: If a database error occurs.
        """
        try:
            prompt = self.db.get(RAGPrompt, prompt_id)
        except exc.SQLAlchemyError as e:
            log.exception(e)
            raise RAGDatabaseError("Error retrieving prompt from database.") from e

        if prompt is None:
            raise RAGPromptValidationError(
                f"Prompt with ID {prompt_id} does not exist."
            )

        changed = False

        if name is not None:
            name = name.strip()
            if not name:
                raise RAGPromptValidationError("Prompt name cannot be empty.")
            if name != prompt.name:
                prompt.name = name
                changed = True

        if parameters is not None:
            if prompt.class_name not in self._registry:
                raise RAGPromptValidationError(
                    f"Component {prompt.class_name} is not registered in the registry."
                )
            prompt_class = self._registry[prompt.class_name]["class"]
            if not issubclass(prompt_class, Prompt):
                raise RAGPromptValidationError(
                    f"Component {prompt.class_name} is not a valid Prompt subclass."
                )

            if "templates" in parameters:
                for _lang, tmpl in parameters["templates"].items():
                    self._validate_prompt_template(prompt.class_name, tmpl)
            elif "template" in parameters:
                self._validate_prompt_template(
                    prompt.class_name, parameters["template"]
                )
            else:
                raise RAGPromptValidationError(
                    "Prompt parameters must include 'template' or 'templates'."
                )
            prompt.parameters = parameters
            prompt.parameters_hash = build_parameters_hash(parameters)
            changed = True

        if not changed:
            return self._serialize_prompt(prompt)

        try:
            self.db.commit()
            self.db.refresh(prompt)
            return self._serialize_prompt(prompt)
        except exc.SQLAlchemyError as e:
            self.db.rollback()
            log.exception(e)
            raise RAGDatabaseError("Error updating prompt in database.") from e

    def get_all(self) -> list[PromptResponse]:
        """Get all prompts.

        Seeds default prompts (DefaultRAGGenerationPrompt and
        DefaultQARAGGenerationPrompt) if the DB is empty.

        Returns:
            A list of serialized prompt responses.

        Raises:
            RAGDatabaseError: If a database error occurs.
        """
        try:
            prompts = self.db.query(RAGPrompt).all()

            if len(prompts) == 0:
                gen_params = {
                    "templates": DefaultRAGGenerationPrompt.metadata["templates"],
                    "language": "en",
                }
                qa_params = {
                    "templates": DefaultQARAGGenerationPrompt.metadata["templates"],
                    "language": "en",
                }
                default_generation_prompt = RAGPrompt(
                    class_name=DefaultRAGGenerationPrompt.__name__,
                    name="Default RAG Generation Prompt",
                    parameters=gen_params,
                    parameters_hash=build_parameters_hash(gen_params),
                )
                default_qa_prompt = RAGPrompt(
                    class_name=DefaultQARAGGenerationPrompt.__name__,
                    name="Default QA RAG Generation Prompt",
                    parameters=qa_params,
                    parameters_hash=build_parameters_hash(qa_params),
                )
                self.db.add(default_generation_prompt)
                self.db.add(default_qa_prompt)
                self.db.commit()
                prompts = self.db.query(RAGPrompt).all()

            return [self._serialize_prompt(p) for p in prompts]

        except exc.SQLAlchemyError as e:
            log.exception(e)
            raise RAGDatabaseError("Error listing prompts in database.") from e

    def create_session_copy(
        self,
        prompt_id: int,
        session_id: int,
        parameters: dict[str, Any] | None = None,
        name: str | None = None,
    ) -> PromptResponse:
        """Create a session-scoped copy of a prompt.

        Adds ``cloned_for_session`` to the parameters dict to avoid UNIQUE
        constraint collisions. Generates a unique name and updates the
        session's parameters dict with the new prompt_id.

        Args:
            prompt_id: Primary key of the prompt to copy.
            session_id: Target session id.
            parameters: Override parameters for the copy (optional).
            name: Override name for the copy (optional).

        Returns:
            The newly created prompt response.

        Raises:
            RAGPromptValidationError: If the prompt or session does not exist.
            RAGDatabaseError: If a database error occurs.
        """
        try:
            existing_prompt = self.db.get(RAGPrompt, prompt_id)
        except exc.SQLAlchemyError as e:
            log.exception(e)
            raise RAGDatabaseError("Error retrieving prompt from database.") from e

        if existing_prompt is None:
            raise RAGPromptValidationError(
                f"Prompt with ID {prompt_id} does not exist."
            )

        try:
            session = self.db.get(GenerativeSession, session_id)
        except exc.SQLAlchemyError as e:
            log.exception(e)
            raise RAGDatabaseError("Error retrieving session from database.") from e

        if session is None:
            raise RAGPromptValidationError(
                f"GenerativeSession with ID {session_id} not found."
            )

        if parameters is not None:
            if "templates" in parameters:
                for _lang, tmpl in parameters["templates"].items():
                    self._validate_prompt_template(existing_prompt.class_name, tmpl)
            elif "template" in parameters:
                self._validate_prompt_template(
                    existing_prompt.class_name, parameters["template"]
                )
            else:
                raise RAGPromptValidationError(
                    "Prompt parameters must include 'template' or 'templates'."
                )
            new_parameters = parameters
        else:
            new_parameters = existing_prompt.parameters

        new_parameters = dict(new_parameters or {})
        new_parameters["cloned_for_session"] = session_id

        base_name = (name or existing_prompt.name or existing_prompt.class_name).strip()
        new_name = self._build_session_prompt_name(base_name, session_id)

        try:
            params_hash = build_parameters_hash(new_parameters)
            new_prompt = RAGPrompt(
                class_name=existing_prompt.class_name,
                name=new_name,
                parameters=new_parameters,
                parameters_hash=params_hash,
            )
            self.db.add(new_prompt)
            self.db.commit()
            self.db.refresh(new_prompt)

            session_parameters = dict(session.parameters or {})
            session_parameters["prompt_id"] = new_prompt.id
            session.parameters = session_parameters
            session.last_modified = datetime.now()
            self.db.add(
                GenerativeSessionParameterHistory(
                    session_id=session.id,
                    parameters=session_parameters,
                    modified_at=datetime.now(),
                )
            )
            self.db.commit()
            self.db.refresh(session)

            return self._serialize_prompt(new_prompt)

        except exc.SQLAlchemyError as e:
            self.db.rollback()
            log.exception(e)
            raise RAGDatabaseError("Error creating session copy in database.") from e

    def validate_template(self, class_name: str, template: str) -> None:
        """Validate a template against the prompt class's required placeholders.

        Parameters
        ----------
        class_name : str
            Registered prompt component name.
        template : str
            The template string to validate.

        Raises
        ------
        ValueError
            If the component is not registered, is not a Prompt subclass,
            or the template is missing required placeholders.
        """
        self._validate_prompt_template(class_name, template)

    def resolve_prompt_id_to_component(self, prompt_id: int) -> dict[str, Any]:
        """Resolve a prompt_id to a component configuration dict.

        Args:
            prompt_id: Primary key of the prompt.

        Returns:
            ``{"component": class_name, "params": {"template": ..., "language": ...}}``
            suitable for pipeline configuration.

        Raises:
            RAGPromptValidationError: If the prompt does not exist or has no
                usable template.
            RAGDatabaseError: If a database error occurs.
        """
        try:
            prompt = self.db.get(RAGPrompt, prompt_id)
        except exc.SQLAlchemyError as e:
            log.exception(e)
            raise RAGDatabaseError("Error retrieving prompt from database.") from e

        if prompt is None:
            raise RAGPromptValidationError(
                f"Prompt with ID {prompt_id} does not exist."
            )

        params = prompt.parameters or {}
        template = params.get("template")
        if not template:
            if "templates" not in params:
                raise RAGPromptValidationError(
                    f"Prompt {prompt_id} has no 'template' or 'templates'"
                )
            language = params.get("language", "en")
            templates = params["templates"]
            template = templates.get(language)
            if not template:
                template = next(iter(templates.values()), None)
        if not template:
            raise RAGPromptValidationError(f"Prompt {prompt_id} has no usable template")

        language = params.get("language", "en")

        return {
            "component": prompt.class_name,
            "params": {
                "template": template,
                "language": language,
            },
        }

    def validate_component_ref(self, prompt_ref: dict[str, Any]) -> None:
        """Validate a prompt component reference.

        Validates that:
        - The prompt reference contains a registered ``component`` name.
        - If a ``template`` is provided, it contains all required placeholders.
        - If no template is provided, the component has a built-in default.

        Parameters
        ----------
        prompt_ref : dict
            ``{"component": "...", "params": {"template": "...", ...}}``

        Raises
        ------
        RAGPromptValidationError
            If validation fails.
        """
        if "component" not in prompt_ref:
            raise RAGPromptValidationError("Prompt config must contain 'component'.")

        component = prompt_ref.get("component", "")
        params = prompt_ref.get("params", {})
        template = params.get("template", "")
        if not template and "templates" in params:
            template = next(iter(params["templates"].values()), "")
        # If no explicit template, the component has a built-in default.
        # Only validate if the caller provided a template to override.
        if template:
            self._validate_prompt_template(component, template)

    def validate_prompt_exists(self, prompt_id: int) -> None:
        """Validate that a prompt ID exists in the database.

        Parameters
        ----------
        prompt_id : int

        Raises
        ------
        RAGPromptValidationError
            If the prompt does not exist.
        """
        prompt = self.db.get(RAGPrompt, prompt_id)
        if prompt is None:
            raise RAGPromptValidationError(
                f"Prompt with ID {prompt_id} does not exist."
            )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _validate_prompt_template(self, class_name: str, template: str) -> None:
        """Check class is registered, is a Prompt subclass, and template validates.

        Args:
            class_name: Registered prompt component name.
            template: The template string to validate.

        Raises:
            RAGPromptValidationError: On any validation failure.
        """
        if class_name not in self._registry:
            raise RAGPromptValidationError(
                f"Component {class_name} is not registered in the registry."
            )

        prompt_component = self._registry[class_name]
        prompt_class = prompt_component["class"]

        if not issubclass(prompt_class, Prompt):
            raise RAGPromptValidationError(
                f"Component {class_name} is not a valid Prompt subclass."
            )

        if not prompt_class.validate_template(template):
            raise RAGPromptValidationError(
                f"Invalid template for prompt {class_name}. "
                f"Required tokens are: {prompt_class.get_required_placeholders()}"
            )

    def _serialize_prompt(self, prompt: RAGPrompt) -> PromptResponse:
        """Convert a RAGPrompt DB model to a PromptResponse."""
        return PromptResponse(
            id=prompt.id,
            class_name=prompt.class_name,
            name=prompt.name,
            parameters=prompt.parameters,
            created=prompt.created,
            last_modified=prompt.last_modified,
        )

    def _build_session_prompt_name(self, base_name: str, session_id: int) -> str:
        """Generate a unique name for a session-scoped prompt copy."""
        candidate = f"{base_name} - session {session_id}"
        suffix = 2
        while self.db.execute(
            select(RAGPrompt.id).where(RAGPrompt.name == candidate)
        ).scalar():
            candidate = f"{base_name} - session {session_id} ({suffix})"
            suffix += 1
        return candidate
