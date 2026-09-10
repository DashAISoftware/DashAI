import { useEffect, useRef, useState } from "react";
import PropTypes from "prop-types";
import { useSnackbar } from "notistack";
import { useTranslation } from "react-i18next";

import { renameDatasetColumn } from "../../../api/datasets";

export default function LeanColumnNameEditor({
  columnName,
  allColumnKeys,
  datasetId,
  onCommit,
  onCancel,
}) {
  const [value, setValue] = useState(columnName);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState("");
  const inputRef = useRef(null);
  const { enqueueSnackbar } = useSnackbar();
  const { t } = useTranslation(["datasets"]);

  useEffect(() => {
    inputRef.current?.focus();
    inputRef.current?.select();
  }, []);

  const submit = async () => {
    const next = value.trim();
    if (!next || next === columnName) {
      onCancel();
      return;
    }
    if (allColumnKeys.includes(next)) {
      setError(t("datasets:table.nameAlreadyExists"));
      return;
    }
    setPending(true);
    try {
      await renameDatasetColumn(datasetId, columnName, next);
      onCommit();
    } catch (e) {
      enqueueSnackbar(t("datasets:table.failedToRename", { columnName }), {
        variant: "error",
      });
      setPending(false);
    }
  };

  return (
    <div className="lean-rename-wrap">
      <input
        ref={inputRef}
        className="lean-rename-input"
        type="text"
        value={value}
        disabled={pending}
        onChange={(e) => {
          setValue(e.target.value);
          if (error) setError("");
        }}
        onClick={(e) => e.stopPropagation()}
        onKeyDown={(e) => {
          if (e.key === "Enter") {
            e.preventDefault();
            submit();
          } else if (e.key === "Escape") {
            e.preventDefault();
            onCancel();
          }
        }}
        onBlur={submit}
      />
      {error && <div className="lean-rename-error">{error}</div>}
    </div>
  );
}

LeanColumnNameEditor.propTypes = {
  columnName: PropTypes.string.isRequired,
  allColumnKeys: PropTypes.arrayOf(PropTypes.string).isRequired,
  datasetId: PropTypes.oneOfType([PropTypes.number, PropTypes.string])
    .isRequired,
  onCommit: PropTypes.func.isRequired,
  onCancel: PropTypes.func.isRequired,
};
