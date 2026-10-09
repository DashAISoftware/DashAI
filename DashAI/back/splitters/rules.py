"""Rules shared by more than one splitter.

The seed-and-shuffle dependency is the same fact in five splitters, so it is
declared once here rather than copied into each of them. A rule is a stateless
object, so the same instance can appear in several schemas' ``rules`` lists;
each schema still has its field names checked against its own fields at class
definition, so listing it somewhere without a ``shuffle`` field fails loudly.

The alternative would have been a shared base schema, which is a structural
change to five components for one shared sentence. This gets the deduplication
without it.
"""

from DashAI.back.core.schema_fields import F, IsTrue, Relevance
from DashAI.back.core.utils import MultilingualString

__all__ = ["SEED_ONLY_MATTERS_WHEN_SHUFFLING"]

#: ``random_state`` has no effect unless the data is shuffled first.
#:
#: Every splitter that takes both said so in its descriptions, in five
#: languages, and none of them enforced it: the field stayed editable and the
#: value was quietly ignored. As a rule the renderer disables the control and
#: says why, and the sentence comes out of the prose.
SEED_ONLY_MATTERS_WHEN_SHUFFLING = Relevance(
    "random_state",
    when=IsTrue(F("shuffle")),
    effect="disable",
    reason=MultilingualString(
        en="The random state has no effect while shuffling is disabled.",
        es=("El estado aleatorio no tiene efecto mientras la mezcla está desactivada."),
        pt=(
            "O estado aleatório não tem efeito enquanto o embaralhamento está "
            "desativado."
        ),
        de=(
            "Der Zufallszustand hat keine Wirkung, solange das Mischen deaktiviert ist."
        ),
        zh="关闭打乱时，随机状态不起作用。",
    ),
)
