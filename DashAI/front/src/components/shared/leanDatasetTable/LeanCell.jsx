import { memo } from "react";
import PropTypes from "prop-types";

function renderValue(value) {
  if (value == null) return "";
  if (typeof value === "string" && value.startsWith("data:image")) {
    return (
      <img
        src={value}
        alt="img"
        style={{ maxHeight: 48, maxWidth: 48, objectFit: "contain" }}
      />
    );
  }
  return String(value);
}

function highlight(text, query) {
  if (!query) return text;
  const lower = text.toLowerCase();
  const q = query.toLowerCase();
  const parts = [];
  let i = 0;
  while (i < text.length) {
    const idx = lower.indexOf(q, i);
    if (idx === -1) {
      parts.push(text.slice(i));
      break;
    }
    if (idx > i) parts.push(text.slice(i, idx));
    parts.push(
      <mark key={idx} className="lean-mark">
        {text.slice(idx, idx + q.length)}
      </mark>,
    );
    i = idx + q.length;
  }
  return parts;
}

const LeanCell = memo(function LeanCell({
  value,
  query,
  isPinned,
  pinnedOffset,
}) {
  const className = isPinned ? "lean-cell lean-cell--pinned" : "lean-cell";
  const style = isPinned ? { right: pinnedOffset ?? 0 } : undefined;
  const isImage = typeof value === "string" && value.startsWith("data:image");
  if (isImage) {
    return (
      <td className={className} style={style}>
        {renderValue(value)}
      </td>
    );
  }
  const text = value == null ? "" : String(value);
  return (
    <td className={className} style={style} title={text || undefined}>
      {query ? highlight(text, query) : text}
    </td>
  );
});

LeanCell.propTypes = {
  value: PropTypes.any,
  query: PropTypes.string,
  isPinned: PropTypes.bool,
  pinnedOffset: PropTypes.number,
};

export default LeanCell;
