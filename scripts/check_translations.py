"""Check backend MultilingualString translation coverage.

Static (AST-based) analogue of ``npx i18next-cli status`` / ``lint`` for the
Python backend. It scans every ``MultilingualString(...)`` literal under
``DashAI/back`` and reports, per locale, how many instances provide a
translation versus how many fall back to English.

Two modes:

- ``status`` (default): print a coverage table, always exit 0.
- ``lint``: print the offending ``file:line`` locations and exit 1 if any
  required locale is missing a translation (suitable for pre-commit / CI).

Usage
-----
    python scripts/check_translations.py            # status table
    python scripts/check_translations.py lint       # fail on any gap
    python scripts/check_translations.py lint --lang zh   # only check zh
"""

import argparse
import ast
import os
import sys
from collections import Counter
from typing import List, Optional, Tuple

# en is the required source language; these are the translation targets.
TARGET_LANGS = ["es", "pt", "de", "zh"]

# Class attributes whose plain-string (non-MultilingualString) values would be
# user-facing and therefore should be flagged. Empty-string base-class defaults
# are ignored (they are overridden by concrete components).
LABEL_ATTRS = {"DISPLAY_NAME", "DESCRIPTION", "SHORT_DESCRIPTION"}


def _func_name(call: ast.Call) -> Optional[str]:
    """Return the called function's bare name, or None.

    Parameters
    ----------
    call : ast.Call
        The call node to inspect.

    Returns
    -------
    Optional[str]
        ``Name.id`` or ``Attribute.attr`` of the callee, else None.
    """
    func = call.func
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        return func.attr
    return None


def _is_str_literal(node: ast.AST) -> bool:
    """Return True if node is a string literal or concat of string literals.

    Parameters
    ----------
    node : ast.AST
        Expression node to test.

    Returns
    -------
    bool
        True for ``"x"`` and ``"a" + "b"`` / implicit adjacency.
    """
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return True
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        return _is_str_literal(node.left) and _is_str_literal(node.right)
    return False


def _is_real_multilingual(call: ast.Call) -> bool:
    """Return True for a hand-authored MultilingualString literal.

    Excludes runtime constructions such as ``MultilingualString(**data)`` or
    ``MultilingualString(en=fallback_title)`` where ``en`` is not a literal,
    which are infrastructure fallbacks rather than translatable content.

    Parameters
    ----------
    call : ast.Call
        A call already known to target ``MultilingualString``.

    Returns
    -------
    bool
        True if the call has a literal ``en=`` string and no ``**`` unpacking.
    """
    if any(kw.arg is None for kw in call.keywords):  # **unpacking
        return False
    en = next((kw.value for kw in call.keywords if kw.arg == "en"), None)
    return en is not None and _is_str_literal(en)


def scan(back_dir: str) -> Tuple[List, List, List]:
    """Scan the backend tree for coverage and plain-string labels.

    Parameters
    ----------
    back_dir : str
        Path to the ``DashAI/back`` directory.

    Returns
    -------
    tuple of list
        ``(instances, plain_labels, no_en)`` where ``instances`` is a list of
        ``(path, lineno, set_of_present_target_langs)``, ``plain_labels`` is a
        list of ``(path, lineno, attr)`` user-facing en-only literals, and
        ``no_en`` is a list of ``(path, lineno)`` literals lacking ``en``.
    """
    instances: List[Tuple[str, int, set]] = []
    plain_labels: List[Tuple[str, int, str]] = []
    no_en: List[Tuple[str, int]] = []

    for root, _, files in os.walk(back_dir):
        for fn in files:
            if not fn.endswith(".py"):
                continue
            path = os.path.join(root, fn)
            try:
                with open(path, encoding="utf-8") as fh:
                    tree = ast.parse(fh.read(), filename=path)
            except (SyntaxError, UnicodeDecodeError):
                continue

            for node in ast.walk(tree):
                if (
                    isinstance(node, ast.Call)
                    and _func_name(node) == "MultilingualString"
                ):
                    kws = {kw.arg for kw in node.keywords if kw.arg}
                    has_unpack = any(kw.arg is None for kw in node.keywords)
                    if "en" not in kws and not has_unpack:
                        no_en.append((path, node.lineno))
                    if _is_real_multilingual(node):
                        present = {lang for lang in TARGET_LANGS if lang in kws}
                        instances.append((path, node.lineno, present))

                # Plain (en-only) user-facing labels, excluding "" defaults.
                if isinstance(node, (ast.Assign, ast.AnnAssign)):
                    if isinstance(node, ast.Assign):
                        targets = node.targets
                    else:
                        targets = [node.target]
                    value = node.value
                    for tgt in targets:
                        if (
                            isinstance(tgt, ast.Name)
                            and tgt.id in LABEL_ATTRS
                            and value is not None
                            and _is_str_literal(value)
                            and not (
                                isinstance(value, ast.Constant) and value.value == ""
                            )
                        ):
                            plain_labels.append((path, node.lineno, tgt.id))

    return instances, plain_labels, no_en


def _bar(pct: float, width: int = 20) -> str:
    """Render an ASCII progress bar for the given percentage.

    Parameters
    ----------
    pct : float
        Percentage in the range [0, 100].
    width : int
        Total bar width in characters.

    Returns
    -------
    str
        A bar like ``[#######-------------]``.
    """
    filled = round(pct / 100 * width)
    return "[" + "#" * filled + "-" * (width - filled) + "]"


def main() -> int:
    """Entry point.

    Returns
    -------
    int
        Process exit code (0 on success, 1 on lint failure, 2 on bad args).
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "mode",
        nargs="?",
        default="status",
        choices=["status", "lint"],
        help="status: print coverage (exit 0). lint: fail on gaps (exit 1).",
    )
    parser.add_argument(
        "--lang",
        action="append",
        choices=TARGET_LANGS,
        help="Restrict to one or more locales (repeatable). Default: all.",
    )
    parser.add_argument(
        "--back-dir",
        default=os.path.join("DashAI", "back"),
        help="Path to the backend package (default: DashAI/back).",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=40,
        help="Max file rows to list in lint mode (0 = unlimited).",
    )
    args = parser.parse_args()

    langs = args.lang or TARGET_LANGS

    if not os.path.isdir(args.back_dir):
        print(f"ERROR: backend dir not found: {args.back_dir}", file=sys.stderr)
        return 2

    instances, plain_labels, no_en = scan(args.back_dir)
    total = len(instances)

    print("Backend translation Status")
    print("-" * 40)
    print(f"MultilingualString literals: {total}")
    print("Primary language:            en")
    print(f"Target locales:              {', '.join(langs)}")
    print()
    print("Translation Progress:")
    missing_by_lang = {}
    for lang in langs:
        covered = sum(1 for _, _, present in instances if lang in present)
        missing = total - covered
        missing_by_lang[lang] = missing
        pct = 100.0 if total == 0 else covered / total * 100
        print(f"- {lang}: {_bar(pct)} {pct:5.1f}% ({covered}/{total} literals)")

    total_missing = sum(missing_by_lang.values())

    if plain_labels:
        print()
        print(f"Plain en-only labels (not MultilingualString): {len(plain_labels)}")
    if no_en:
        print()
        print(f"WARNING: MultilingualString literals without 'en': {len(no_en)}")
        for path, lineno in no_en:
            print(f"  {path.replace(os.sep, '/')}:{lineno}")

    if args.mode == "status":
        return 0

    # lint mode
    if total_missing == 0 and not no_en:
        print()
        print("OK: no missing translations.")
        return 0

    print()
    print("Missing translations by file:")
    by_file = Counter()
    for path, _, present in instances:
        gaps = [lang for lang in langs if lang not in present]
        if gaps:
            by_file[path.replace(os.sep, "/")] += len(gaps)

    rows = by_file.most_common()
    shown = rows if args.limit == 0 else rows[: args.limit]
    for rel, count in shown:
        print(f"  {count:4d}  {rel}")
    if len(rows) > len(shown):
        print(f"  ... and {len(rows) - len(shown)} more files")

    print()
    print(
        f"FAIL: {total_missing} missing translation(s) across {len(by_file)} file(s)."
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
