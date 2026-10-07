export const KIND_ORDER = [
  "title",
  "heading",
  "paragraph",
  "list_item",
  "table",
  "code",
  "quote",
  "caption",
  "image",
  "page_header",
  "page_footer",
];

export const HIDDEN_KINDS = new Set(["page_header", "page_footer"]);

const KIND_FAMILIES = {
  title: "heading",
  heading: "heading",
  table: "table",
  code: "code",
  image: "image",
};

export function kindColor(theme, kind) {
  const accents = theme.palette.accent;
  switch (KIND_FAMILIES[kind]) {
    case "heading":
      return accents.amber;
    case "table":
      return accents.teal;
    case "code":
      return accents.purple;
    case "image":
      return accents.coral;
    default:
      return HIDDEN_KINDS.has(kind)
        ? theme.palette.ui.borderMed
        : theme.palette.text.disabled;
  }
}

export function kindLabel(t, kind) {
  return t(`datasets:document.kind.${kind}`, { defaultValue: kind });
}

export function prefersReducedMotion() {
  return (
    typeof window !== "undefined" &&
    window.matchMedia?.("(prefers-reduced-motion: reduce)").matches
  );
}

export function scrollToPosition(position, highlightColor) {
  const element = document.querySelector(
    `[data-document-position="${position}"]`,
  );
  if (!element) return false;
  const reduced = prefersReducedMotion();
  element.scrollIntoView({
    behavior: reduced ? "auto" : "smooth",
    block: "center",
  });
  if (!reduced && element.animate) {
    element.animate(
      [
        { boxShadow: `0 0 0 3px ${highlightColor}` },
        { boxShadow: "0 0 0 0 transparent" },
      ],
      { duration: 1400, easing: "ease-out" },
    );
  }
  return true;
}
