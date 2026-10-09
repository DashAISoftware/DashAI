import PropTypes from "prop-types";
import { useTranslation } from "react-i18next";

import LeanColumnNameEditor from "./LeanColumnNameEditor";
import LeanEncoderChip from "./LeanEncoderChip";

export default function LeanHeaderCell({
  columnKey,
  type,
  encoder,
  renamable,
  isEditing,
  sortDir,
  allColumnKeys,
  datasetId,
  isPinned,
  pinnedOffset,
  onStartEdit,
  onCommitEdit,
  onCancelEdit,
  onSortClick,
  onEncoderChanged,
}) {
  const { t } = useTranslation(["datasets"]);
  const sortTitle =
    sortDir === "asc"
      ? t("datasets:table.sortedAsc")
      : sortDir === "desc"
        ? t("datasets:table.sortedDesc")
        : t("datasets:table.clickToSort");

  return (
    <th
      className={isPinned ? "lean-th lean-th--pinned" : "lean-th"}
      style={isPinned ? { right: pinnedOffset ?? 0 } : undefined}
    >
      <div className="lean-th-inner">
        <div className="lean-th-name-row">
          {isEditing && renamable ? (
            <LeanColumnNameEditor
              columnName={columnKey}
              allColumnKeys={allColumnKeys}
              datasetId={datasetId}
              onCommit={onCommitEdit}
              onCancel={onCancelEdit}
            />
          ) : (
            <div
              className={
                renamable
                  ? "lean-th-name lean-th-name--editable"
                  : "lean-th-name"
              }
              title={
                renamable ? t("datasets:table.doubleClickToRename") : undefined
              }
              onDoubleClick={renamable ? onStartEdit : undefined}
            >
              {columnKey}
            </div>
          )}
          <button
            type="button"
            className={`lean-sort lean-sort--${sortDir ?? "none"}`}
            title={sortTitle}
            onClick={onSortClick}
          >
            <span className="lean-sort-arrow lean-sort-arrow--up">▲</span>
            <span className="lean-sort-arrow lean-sort-arrow--down">▼</span>
          </button>
        </div>
        <div className="lean-th-type">
          <span>{type || null}</span>
          {type === "Categorical" && datasetId && (
            <LeanEncoderChip
              columnName={columnKey}
              encoder={encoder}
              datasetId={datasetId}
              onChanged={onEncoderChanged}
            />
          )}
          {isPinned && (
            <span className="lean-target-chip">
              {t("datasets:table.predictedColumn")}
            </span>
          )}
        </div>
      </div>
    </th>
  );
}

LeanHeaderCell.propTypes = {
  columnKey: PropTypes.string.isRequired,
  type: PropTypes.string,
  encoder: PropTypes.string,
  renamable: PropTypes.bool.isRequired,
  isEditing: PropTypes.bool.isRequired,
  sortDir: PropTypes.oneOf(["asc", "desc", null]),
  allColumnKeys: PropTypes.arrayOf(PropTypes.string).isRequired,
  datasetId: PropTypes.oneOfType([PropTypes.number, PropTypes.string]),
  isPinned: PropTypes.bool,
  pinnedOffset: PropTypes.number,
  onStartEdit: PropTypes.func.isRequired,
  onCommitEdit: PropTypes.func.isRequired,
  onCancelEdit: PropTypes.func.isRequired,
  onSortClick: PropTypes.func.isRequired,
  onEncoderChanged: PropTypes.func,
};
