import { Image as ImageIcon, Notes as TextIcon } from "@mui/icons-material";
import { kindLabel } from "../../documents/documentKinds";

export const CONTENT_TYPE_ICONS = {
  Text: TextIcon,
  Image: ImageIcon,
};

export function contentTypeLabel(t, typeName) {
  return t(`datasets:documentNotebook.contentType.${typeName}`, {
    defaultValue: typeName,
  });
}

export function describeItemScope(t, column) {
  const type = contentTypeLabel(t, column.columnName);
  const kinds =
    !column.kinds || column.kinds.length === 0
      ? t("datasets:documentNotebook.allKinds")
      : column.kinds.map((kind) => kindLabel(t, kind)).join(", ");
  if (!column.positions || column.positions.length === 0) {
    return `${type}: ${kinds}`;
  }
  return `${type}: ${kinds} (${t("datasets:documentNotebook.pickedItems", {
    positions: column.positions.map((position) => position + 1).join(", "),
  })})`;
}
