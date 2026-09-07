import inspect
from typing import Any, ClassVar, Dict, List, Sequence, Tuple

from pydantic import BaseModel, model_validator

from DashAI.back.core.schema_fields.rules import (
    Rule,
    RuleViolationError,
    rules_to_wire,
    validate_rules,
)
from DashAI.back.core.schema_fields.rules_eval import evaluate_rules
from DashAI.back.core.utils import MultilingualString

#: Root key carrying the serialized rule set. Absent unless a schema declares
#: rules, so every existing schema keeps emitting a byte-identical document.
RULES_KEY = "x-dashai-rules"

#: Cleaned docstring of ``BaseSchema``, filled in below the class definition.
#: pydantic turns a model's docstring into the schema's ``description``, and
#: ``ConfigObject.SCHEMA`` defaults to ``BaseSchema``, so without this every
#: component that forgets to set ``SCHEMA`` serves this module's internal prose
#: to the browser as user-facing text. (Before this file grew a real docstring
#: it served a commented-out method body, which five registered components
#: actually shipped.)
_BASE_DOC: str = ""


def _schema_postprocessor(rules_wire, previous):
    """Build the ``json_schema_extra`` hook for one schema class.

    Composes three jobs so a class only ever needs one hook: preserve whatever
    the author already declared, drop an inherited ``BaseSchema`` description,
    and add the rule set when there is one.

    Parameters
    ----------
    rules_wire : list or None
        Serialized rules, or ``None`` for a schema that declares none. ``None``
        means the key is not written at all, which is what keeps existing
        schemas byte-identical.
    previous : dict, callable or None
        Whatever ``json_schema_extra`` the class already carried.

    Returns
    -------
    callable
        A one-argument hook pydantic calls with the generated schema.
    """

    def _postprocess(schema: Dict[str, Any]) -> None:
        if callable(previous):
            previous(schema)
        elif isinstance(previous, dict):
            schema.update(previous)
        if _BASE_DOC and schema.get("description") == _BASE_DOC:
            schema.pop("description", None)
        if rules_wire:
            schema[RULES_KEY] = rules_wire

    return _postprocess


def replace_defs_in_schema(schema: dict):
    # 1. Resolve $defs if present
    if "$defs" in schema:
        for prop, prop_schema in schema["properties"].items():
            if "$ref" in prop_schema:
                _, _, def_name = prop_schema["$ref"].split("/")
                schema["properties"][prop] = schema["$defs"][def_name]
        schema.pop("$defs")

    # 2. Normalize titles for ALL properties
    for prop, prop_schema in schema["properties"].items():
        # Extract display_name from the property level
        display_name = prop_schema.pop("display_name", None)

        # Also check inside anyOf/oneOf/allOf items
        for key in ["anyOf", "oneOf", "allOf"]:
            if key in prop_schema:
                for item in prop_schema[key]:
                    if "display_name" in item:
                        # Use the first display_name found if not already set
                        if display_name is None:
                            display_name = item.pop("display_name")
                        else:
                            item.pop("display_name")

        # Convert display_name to MultilingualString title
        if isinstance(display_name, MultilingualString):
            prop_schema["title"] = display_name
        elif isinstance(display_name, dict):
            prop_schema["title"] = MultilingualString(**display_name)
        elif isinstance(prop_schema.get("title"), MultilingualString):
            # already correct
            pass
        else:
            # fallback: derive from property name
            fallback_title = prop.replace("_", " ").title()
            prop_schema["title"] = MultilingualString(en=fallback_title)

    return schema


class BaseSchema(BaseModel):
    """Base class for every component parameter schema.

    Besides the pydantic fields a component declares, a schema may declare
    ``rules``: relations between fields that no per-field keyword can express.
    See ``DashAI.back.core.schema_fields.rules`` for the authoring API.

    Rules are declared as a plain class attribute::

        class CharacterChunkModelSchema(BaseSchema):
            chunk_size: schema_field(int_field(gt=1), placeholder=500, ...)
            chunk_overlap: schema_field(int_field(gt=0), placeholder=50, ...)

            rules = [
                Check(
                    Lt("chunk_overlap", "chunk_size"),
                    id="chunker.overlap_under_size",
                    targets=["chunk_overlap"],
                    message=MultilingualString(en="...", es="..."),
                ),
            ]

    and that single declaration is enforced twice. On the server an inherited
    ``model_validator`` runs it, so every existing ``SCHEMA.model_validate``
    call site gains the check for free. On the wire it is serialized into the
    ``x-dashai-rules`` root key, which the browser replays with the same
    semantics so the user sees the error before submitting.

    Two semantics worth knowing when writing rules:

    * A subclass's rules are **merged** with its parents', parents first. 25
      in-tree schemas subclass another schema, and silently discarding an
      inherited rule would be a dead constraint nobody notices.
    * A rule that cannot be judged yet, because a field it reads is empty or
      because it needs a dataset context that was not supplied, is *pending*
      rather than satisfied. Pending rules are reported, never dropped.
    """

    #: Rules declared by this schema. Subclasses assign a plain list; the
    #: ClassVar annotation here is what keeps pydantic from treating it as a
    #: field.
    rules: ClassVar[Sequence[Rule]] = ()

    #: Merged rules for this class, parents first. Set by
    #: ``__pydantic_init_subclass__``; do not assign it by hand.
    __dashai_rules__: ClassVar[Tuple[Rule, ...]] = ()

    @classmethod
    def __pydantic_init_subclass__(cls, **kwargs: Any) -> None:
        """Merge, check and publish this schema's rules.

        Runs once per subclass, at class-definition time, which is what makes a
        misspelled field name an import-time error instead of a constraint that
        silently never fires.
        """
        super().__pydantic_init_subclass__(**kwargs)

        inherited: Tuple[Rule, ...] = ()
        for base in cls.__mro__[1:]:
            found = base.__dict__.get("__dashai_rules__")
            if found is not None:
                inherited = found
                break

        own = cls.__dict__.get("rules") or ()
        if isinstance(own, Rule):
            own = (own,)
        merged = tuple(inherited) + tuple(own)
        cls.__dashai_rules__ = merged

        if own:
            validate_rules(
                own,
                owner=cls.__name__,
                known=cls.model_fields.keys(),
                unreadable=_optimizer_fields(cls),
            )

        previous = cls.model_config.get("json_schema_extra")
        cls.model_config = {
            **cls.model_config,
            "json_schema_extra": _schema_postprocessor(
                rules_to_wire(merged) if merged else None, previous
            ),
        }

    @model_validator(mode="after")
    def _dashai_check_rules(self) -> "BaseSchema":
        """Enforce the declared rules on the server.

        Rules needing a dataset context are skipped here and reported as
        unvalidated: this validator has no context to give them. Endpoints that
        can build one call ``check_rules`` directly.

        Raises
        ------
        RuleViolationError
            Wrapped by pydantic into a ``ValidationError``, so every existing
            caller that catches ``ValidationError`` keeps working unchanged.
        """
        rules = type(self).__dashai_rules__
        if not rules:
            return self
        report = check_rules(type(self), self.model_dump(), ctx=None)
        if report.violations:
            first = report.violations[0]
            error = RuleViolationError(
                first["rule_id"], first["targets"], first["message"]
            )
            # Every violation, not just the first: pydantic can only carry one
            # error out of a model validator, but an endpoint building a
            # per-field payload wants them all.
            error.all_violations = report.violations
            raise error
        return self


_BASE_DOC = inspect.cleandoc(BaseSchema.__doc__ or "")

# ``__pydantic_init_subclass__`` never runs for BaseSchema itself, so wire its
# own hook here. Without this, the components whose ``SCHEMA`` defaults to
# BaseSchema would still ship this class's docstring as their description.
BaseSchema.model_config = {
    **BaseSchema.model_config,
    "json_schema_extra": _schema_postprocessor(None, None),
}


def _optimizer_fields(schema_cls: type) -> List[str]:
    """Fields whose value is the search envelope rather than a scalar.

    A rule that reads one of these can only ever be pending: the value is a
    ``SearchSpace``, and the algebra refuses a non-number by design. Giving the
    search space a declared type did not change that, so the guard stays.

    ``search_space`` says so with its own key. The placeholder shape is still
    checked as well, because that is all a plugin declaring the envelope by
    hand has to go on, and such a rule has to be refused just the same.
    """
    from DashAI.back.core.schema_fields.search_space import SEARCH_DTYPE_KEY

    found = []
    for name, field in schema_cls.model_fields.items():
        extra = field.json_schema_extra
        if not isinstance(extra, dict):
            continue
        if extra.get(SEARCH_DTYPE_KEY) is not None:
            found.append(name)
            continue
        placeholder = extra.get("placeholder")
        if isinstance(placeholder, dict) and "optimize" in placeholder:
            found.append(name)
    return found


def check_rules(schema_cls: type, values: Dict[str, Any], ctx: Any = None):
    """Evaluate a schema class's rules against a set of values.

    The entry point for callers that can supply a context, such as an endpoint
    that knows which dataset the user selected. Without a context, rules
    declaring ``requires_ctx`` are reported as pending rather than passed.

    Parameters
    ----------
    schema_cls : type
        A ``BaseSchema`` subclass.
    values : dict
        Field values to judge.
    ctx : mapping, optional
        Facts from outside the schema (dataset columns, row count, ...).

    Returns
    -------
    RuleReport
    """
    rules = getattr(schema_cls, "__dashai_rules__", ())
    return evaluate_rules(rules_to_wire(rules), values, ctx)


def violations_payload(error: Exception) -> List[Dict[str, Any]]:
    """Extract every rule violation carried by a raised error.

    Lets an endpoint answer with a per-field, localizable payload instead of
    stringifying a pydantic ``ValidationError`` into an HTTP detail, which is
    how ``errors.pydantic.dev`` URLs currently end up in front of users.
    """
    violations = getattr(error, "all_violations", None)
    if violations is not None:
        return violations
    if isinstance(error, RuleViolationError):
        return [error.as_payload()]
    return []
