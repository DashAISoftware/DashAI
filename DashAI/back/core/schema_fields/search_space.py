"""A hyperparameter the user can either fix or hand to the optimizer.

Until now this was not a type at all. A field was made optimizable by giving it
a placeholder shaped like a dict:

.. code-block:: python

    C: schema_field(
        optimizer_float_field(gt=0.0),
        placeholder={
            "optimize": False,
            "fixed_value": 1.0,
            "lower_bound": 1.0,
            "upper_bound": 10.0,
        },
        description=...,
    )

The placeholder was the only carrier of the signal: the renderer decides
whether to draw the optimize toggle by asking whether the placeholder has an
``optimize`` key, and ``optimizer_float_field`` is byte-for-byte
``float_field``, so the name declares an intent that nothing acts on. Two
consequences followed, both measured across the tree:

* Thirty-one fields are declared with ``optimizer_*`` wrapped in ``none_type``,
  which forces ``placeholder=None``. The signal is erased, so the toggle never
  appears and the parameter cannot be optimized however it was declared.
* No component's schema accepts its own declared placeholders: all thirty-one
  that have optimizable fields fail ``SCHEMA.model_validate`` on them, because
  the envelope is a dict the field's type knows nothing about.

Here the search space becomes the field's type. The four-key envelope that is
already in the database stays exactly as it is, so nothing has to be migrated,
but now it is validated: ``lower_bound < upper_bound`` is enforced where the
value lives rather than in a yup test, the bounds are checked against the
field's own constraints, and a misspelled key is rejected instead of ignored.

The placeholder is derived from the declaration, so there is no dict to write
by hand and no way for it to disagree with the field it describes:

.. code-block:: python

    C: search_space(float_field(gt=0.0), fixed=1.0, low=1.0, high=10.0, description=...)

Making it a type is also what lets a search space be something other than an
interval. ``lower_bound``/``upper_bound`` is a vocabulary that can only
describe a scale, and ``hinge`` is not between ``squared_hinge`` and anything
else, so a categorical parameter had no way to say what it wanted. A search
space is now either an interval or a set of choices, which covers the 38 enum
and 18 boolean fields that sit in components already doing numeric search.
"""

from typing import Any, Generic, List, Optional, Type, TypeVar, Union, get_args

from pydantic import (
    BaseModel,
    Field,
    TypeAdapter,
    ValidationError,
    WithJsonSchema,
    model_validator,
)
from typing_extensions import Annotated, get_origin

from DashAI.back.core.utils import MultilingualString

__all__ = [
    "SEARCH_DTYPE_KEY",
    "SearchSpace",
    "SearchSpaceDeclarationError",
    "search_space",
]

T = TypeVar("T")

#: Where the emitted schema says what kind of space this is.
#:
#: The renderer and ``ModelFactory`` used to read the JSON Schema ``type`` key
#: to decide which distribution to ask the optimizer for. That key is absent
#: whenever a field admits null, because pydantic emits ``anyOf`` instead, and
#: it cannot express "categorical" at all. This one is declared rather than
#: inferred, so it survives both.
SEARCH_DTYPE_KEY = "x-dashai-search-dtype"


class SearchSpace(BaseModel, Generic[T]):
    """The value the form sends and the database stores, with a type.

    The shape is the one already persisted, so existing runs keep loading. What
    is new is that it is checked. ``T`` is the field's own inner type, so the
    bounds and the choices are validated against the same constraints as the
    value itself: a lower bound of ``-5`` on a field declared ``gt=0`` is now
    an error naming that key instead of a search that proposes values the field
    would reject.

    Exactly one of the two shapes may be filled in when ``optimize`` is set:

    * ``lower_bound`` and ``upper_bound`` for something measured on a scale.
    * ``choices`` for something picked out of a set.
    """

    model_config = {"extra": "forbid"}

    optimize: bool = False
    fixed_value: Optional[T] = None
    lower_bound: Optional[T] = None
    upper_bound: Optional[T] = None
    choices: Optional[List[T]] = None

    @model_validator(mode="before")
    @classmethod
    def _lift_bare_value(cls, data: Any) -> Any:
        """A bare value means a parameter fixed at that value.

        ``ModelFactory`` unwraps the envelope before instantiating a model, so
        a model's own ``__init__`` receives plain scalars and validates them
        through ``validate_and_transform``. Accepting a scalar here keeps that
        path working, and lets the field be declared as one type rather than a
        union, which is what keeps the error messages pointed at the key that
        is actually wrong.
        """
        if isinstance(data, (dict, SearchSpace)):
            return data
        return {"optimize": False, "fixed_value": data}

    @model_validator(mode="after")
    def _coherent(self) -> "SearchSpace":
        if not self.optimize:
            if "fixed_value" not in self.model_fields_set:
                # Absent, not null: a field that admits None can be fixed at
                # None, which is what `max_depth` means by "no limit".
                raise ValueError("a fixed parameter needs a fixed_value")
            return self

        interval = self.lower_bound is not None or self.upper_bound is not None
        categorical = self.choices is not None

        if interval and categorical:
            raise ValueError(
                "a search space is either an interval (lower_bound and "
                "upper_bound) or a set of choices, not both"
            )
        if not interval and not categorical:
            raise ValueError(
                "an optimized parameter needs either both bounds or a list of choices"
            )
        if categorical:
            if len(self.choices) < 2:
                raise ValueError(
                    "a categorical search needs at least two choices; with one "
                    "there is nothing to search"
                )
            if len(self.choices) != len(set(self.choices)):
                raise ValueError("the choices must be distinct")
        else:
            if self.lower_bound is None or self.upper_bound is None:
                raise ValueError(
                    "an interval search needs both lower_bound and upper_bound"
                )
            if self.lower_bound >= self.upper_bound:
                raise ValueError(
                    f"lower_bound must be below upper_bound, got "
                    f"{self.lower_bound} and {self.upper_bound}"
                )
        return self

    def resolve(self) -> Optional[T]:
        """The value to use when nobody is going to optimize this parameter.

        ``fill_objects`` calls this so the library underneath receives the
        number or the option it expects rather than the envelope.
        """
        return self.fixed_value


class SearchSpaceDeclarationError(TypeError):
    """A declaration that does not hold up against the field's own constraints.

    Raised while the class body is being evaluated, so a contradiction between
    a field's bounds and the range declared for it fails at import instead of
    at some trial in the middle of a study.
    """


def _unwrap(annotation: Type) -> Type:
    """The type under ``Annotated`` and ``Optional`` wrappers."""
    while True:
        if get_origin(annotation) is Annotated:
            annotation = get_args(annotation)[0]
            continue
        if get_origin(annotation) is Union:
            members = [a for a in get_args(annotation) if a is not type(None)]
            if len(members) == 1:
                annotation = members[0]
                continue
        return annotation


def _options_of(inner: Type) -> Optional[List[Any]]:
    """The declared options, when the inner field is picked from a set.

    An ``enum_field`` says so in its emitted schema. A boolean says it by being
    a boolean: there are exactly two values and neither is between the other,
    which is the same situation an enum is in.

    ``None`` counts as an option when the field admits it, because for these
    parameters it is a value and not an absence. sklearn's ``class_weight`` is
    declared ``none_type(enum_field(["balanced"]))``, and unweighted against
    balanced is exactly the comparison worth searching; read as a one-option
    enum it would look like nothing to search at all.
    """
    if _unwrap(inner) is bool:
        return [False, True]
    try:
        schema = TypeAdapter(inner).json_schema()
    except Exception:
        return None
    if "enum" in schema:
        return list(schema["enum"])
    branches = schema.get("anyOf", ())
    nullable = any(branch.get("type") == "null" for branch in branches)
    for branch in branches:
        if "enum" in branch:
            options = list(branch["enum"])
            return [None, *options] if nullable else options
    if nullable and any(branch.get("type") == "boolean" for branch in branches):
        return [None, False, True]
    return None


def _dtype_of(inner: Type, options: Optional[List[Any]]) -> str:
    if options is not None:
        return "categorical"
    return "integer" if _unwrap(inner) is int else "number"


def search_space(
    inner: Type,
    *,
    fixed: Any,
    low: Any = None,
    high: Any = None,
    choices: Optional[List[Any]] = None,
    description: Union[str, MultilingualString],
    alias: Union[str, MultilingualString, None] = None,
) -> Type:
    """Declare a hyperparameter the user may fix or hand to the optimizer.

    Replaces the ``optimizer_*_field`` plus hand-written ``placeholder`` pair,
    and does the job of ``schema_field`` for this one case, because the
    placeholder is derived rather than passed.

    Parameters
    ----------
    inner
        The field the value has to satisfy, declared exactly as it would be
        without any search: ``float_field(gt=0.0)``, ``int_field(ge=1)``,
        ``enum_field([...])``, ``bool_field()``, or any of those under
        ``none_type``.
    fixed
        The value to start from, and the value used whenever the parameter is
        not being optimized.
    low, high
        The interval to search, for a numeric field. ``low`` must be below
        ``high``, and both must satisfy ``inner``.
    choices
        The options to search, for an enum or boolean field. Defaults to every
        option the field declares, which is usually what is wanted.
    description, alias
        As in ``schema_field``.

    Raises
    ------
    SearchSpaceDeclarationError
        If the declaration contradicts itself: a range whose ends the field
        would reject, ``low`` at or above ``high``, an interval over a set of
        options, or a set of choices for something measured on a scale.
    """
    options = _options_of(inner)
    dtype = _dtype_of(inner, options)
    adapter = TypeAdapter(inner)

    if dtype == "categorical":
        if low is not None or high is not None:
            raise SearchSpaceDeclarationError(
                f"search_space over {options} takes `choices`, not `low`/`high`: "
                "the options are a set, not a scale, so there is nothing for an "
                "interval to mean."
            )
        if choices is None:
            choices = list(options)
        if len(choices) < 2:
            raise SearchSpaceDeclarationError(
                f"search_space(choices={choices!r}): a categorical search needs "
                "at least two options; with one there is nothing to search."
            )
        if len(choices) != len(set(choices)):
            raise SearchSpaceDeclarationError(
                f"search_space(choices={choices!r}): the options repeat."
            )
        checked = (("fixed", fixed),) + tuple(
            (f"choices[{index}]", choice) for index, choice in enumerate(choices)
        )
    else:
        if choices is not None:
            raise SearchSpaceDeclarationError(
                "search_space over a numeric field takes `low`/`high`, not `choices`."
            )
        if low is None or high is None:
            raise SearchSpaceDeclarationError(
                "search_space over a numeric field needs both `low` and `high`."
            )
        checked = (("fixed", fixed), ("low", low), ("high", high))

    for label, value in checked:
        try:
            adapter.validate_python(value)
        except ValidationError as exc:
            raise SearchSpaceDeclarationError(
                f"search_space({label}={value!r}) does not satisfy the field's "
                f"own constraints: {exc.errors()[0]['msg']}. The search would "
                f"propose values the field itself rejects."
            ) from exc

    if dtype != "categorical" and low >= high:
        raise SearchSpaceDeclarationError(
            f"search_space(low={low!r}, high={high!r}): low must be below high."
        )

    if isinstance(description, str):
        description = MultilingualString(en=description)

    # The wire keeps the shape it has today. Left to itself pydantic emits a
    # `$ref` into `$defs` for a generic model, and the renderer reads `type`,
    # `anyOf` and `enum` straight off the property without resolving
    # references, so every optimizable form would go blank. Emitting the inner
    # field's own schema keeps the property byte-identical to what it is now,
    # apart from the added dtype key.
    inner_schema = adapter.json_schema()
    inner_schema.pop("title", None)

    placeholder = {"optimize": False, "fixed_value": fixed}
    if dtype == "categorical":
        placeholder["choices"] = list(choices)
    else:
        placeholder["lower_bound"] = low
        placeholder["upper_bound"] = high

    return Annotated[
        SearchSpace[inner],
        WithJsonSchema(inner_schema),
        Field(
            description=description,
            json_schema_extra={
                "display_name": alias,
                SEARCH_DTYPE_KEY: dtype,
                "placeholder": placeholder,
            },
        ),
    ]
