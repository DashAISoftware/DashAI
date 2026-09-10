import { memo, useCallback, useMemo, useState } from "react";
import { Box, TablePagination, Tooltip, Typography } from "@mui/material";
import { useTheme } from "@mui/material/styles";
import { TypeChangeValidator } from "./TypeChangeValidator";
import InferenceReasonPopover from "../dataset/InferenceReasonPopover";
import EncoderChipBase from "../../shared/leanDatasetTable/EncoderChipBase";
import { useTranslation } from "react-i18next";
import { useSnackbar } from "notistack";

const TYPE_TO_DEFAULT_DTYPE = {
  Integer: "int64",
  Float: "float64",
  Text: "string",
  Categorical: "string",
  Decimal: "decimal128(8, 0)",
  Binary: "binary",
  Image: "string",
};

const TYPE_OPTIONS = [
  "Integer",
  "Float",
  "Text",
  "Categorical",
  "Date",
  "Image",
];

const PAGE_SIZE = 5;

// Plain select styled to blend with the theme - mounted once per column header,
// not once per cell.
const ColumnTypeSelect = memo(function ColumnTypeSelect({
  field,
  value,
  disabled,
  onChange,
  bg,
  color,
}) {
  return (
    <select
      value={value || "Text"}
      disabled={disabled}
      onChange={(e) => onChange(field, e.target.value)}
      style={{
        fontSize: "0.75rem",
        padding: "3px 6px",
        minWidth: 120,
        border: "1px solid rgba(128,128,128,0.4)",
        borderRadius: 4,
        background: bg,
        color,
        cursor: disabled ? "default" : "pointer",
        outline: "none",
      }}
    >
      {TYPE_OPTIONS.map((t) => (
        <option key={t} value={t}>
          {t}
        </option>
      ))}
    </select>
  );
});

ColumnTypeSelect.propTypes = {
  field: (props, propName) => null,
  value: (props, propName) => null,
  disabled: (props, propName) => null,
  onChange: (props, propName) => null,
  bg: (props, propName) => null,
  color: (props, propName) => null,
};

function PreviewDatasetTable({
  rows,
  columnTypes,
  file,
  params,
  onTypeChange,
  onColumnRename,
  onEncoderChange,
}) {
  const { t } = useTranslation(["common"]);
  const { enqueueSnackbar } = useSnackbar();
  const theme = useTheme();

  const [showValidator, setShowValidator] = useState(false);
  const [pendingChanges, setPendingChanges] = useState({});
  const [editingColumn, setEditingColumn] = useState(null);
  const [editValue, setEditValue] = useState("");
  const [columnNames, setColumnNames] = useState({});
  const [page, setPage] = useState(0);

  const encoderLabel = useCallback(
    (enc) => {
      if (enc === "one_hot") return t("common:encoderOneHot");
      if (enc === "label") return t("common:encoderLabel");
      return enc;
    },
    [t],
  );

  const handleTypeChangeRequest = useCallback(
    (field, newType) => {
      const currentType = columnTypes[field]?.type;
      if (currentType === newType) return;
      const currentDtype = columnTypes[field]?.dtype;
      // A Date column's dtype is a strptime format, which only the backend can
      // work out from the values. Sending null asks it to detect one.
      const newDtype =
        newType === "Date"
          ? null
          : newType === "Categorical" && currentDtype
            ? currentDtype
            : TYPE_TO_DEFAULT_DTYPE[newType] || "string";
      setPendingChanges({
        [field]: {
          current_type: currentType,
          new_type: newType,
          new_dtype: newDtype,
        },
      });
      setShowValidator(true);
    },
    [columnTypes],
  );

  const handleConfirmChanges = useCallback(
    (changes) => {
      if (onTypeChange) onTypeChange(changes);
      setShowValidator(false);
      setPendingChanges({});
    },
    [onTypeChange],
  );

  const handleCancelChanges = useCallback(() => {
    setShowValidator(false);
    setPendingChanges({});
  }, []);

  const handleStartEdit = useCallback(
    (columnName) => {
      setEditingColumn(columnName);
      setEditValue(columnNames[columnName] || columnName);
    },
    [columnNames],
  );

  const handleCancelEdit = useCallback(() => {
    setEditingColumn(null);
    setEditValue("");
  }, []);

  const handleConfirmEdit = useCallback(
    (oldName) => {
      const newName = editValue.trim();
      if (!newName) {
        enqueueSnackbar(t("common:columnNameCannotBeEmpty"), {
          variant: "warning",
        });
        handleCancelEdit();
        return;
      }
      const columnNameRegex = /^[a-zA-Z0-9_]+$/;
      if (!columnNameRegex.test(newName)) {
        enqueueSnackbar(t("common:columnNameInvalidCharacters"), {
          variant: "warning",
        });
        handleCancelEdit();
        return;
      }
      if (
        newName === oldName ||
        newName === (columnNames[oldName] || oldName)
      ) {
        handleCancelEdit();
        return;
      }
      const allNames = Object.keys(columnTypes).map(
        (col) => columnNames[col] || col,
      );
      if (allNames.includes(newName)) {
        enqueueSnackbar(t("common:columnNameAlreadyExists"), {
          variant: "warning",
        });
        handleCancelEdit();
        return;
      }
      setColumnNames((prev) => ({ ...prev, [oldName]: newName }));
      if (onColumnRename) onColumnRename(oldName, newName);
      handleCancelEdit();
    },
    [
      editValue,
      columnNames,
      columnTypes,
      onColumnRename,
      t,
      enqueueSnackbar,
      handleCancelEdit,
    ],
  );

  const fields = useMemo(() => {
    if (!rows?.length) return [];
    return Object.keys(rows[0]);
  }, [rows]);

  const pageRows = useMemo(
    () => rows?.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE) ?? [],
    [rows, page],
  );

  const bg = theme.palette.background.paper;
  const color = theme.palette.text.primary;
  const headerBg =
    theme.palette.ui?.panelDark ?? theme.palette.background.default;
  const divider = theme.palette.divider;

  return (
    <>
      <div style={{ overflowX: "auto" }}>
        <table
          style={{
            borderCollapse: "collapse",
            tableLayout: "auto",
            width: "max-content",
            minWidth: "100%",
          }}
        >
          <thead>
            <tr>
              {fields.map((field) => {
                const columnType = columnTypes[field];
                const displayName = columnNames[field] || field;
                return (
                  <th
                    key={field}
                    style={{
                      padding: "6px 12px",
                      background: headerBg,
                      borderBottom: `2px solid ${divider}`,
                      verticalAlign: "top",
                      minWidth: 150,
                      whiteSpace: "nowrap",
                    }}
                  >
                    <Box
                      sx={{
                        display: "flex",
                        flexDirection: "column",
                        alignItems: "flex-start",
                        gap: 1,
                      }}
                    >
                      {editingColumn === field ? (
                        <input
                          autoFocus
                          value={editValue}
                          onChange={(e) => setEditValue(e.target.value)}
                          onKeyDown={(e) => {
                            if (e.key === "Enter") handleConfirmEdit(field);
                            else if (e.key === "Escape") handleCancelEdit();
                          }}
                          onBlur={() => handleConfirmEdit(field)}
                          style={{
                            fontSize: "0.875rem",
                            padding: "3px 6px",
                            border: `1px solid ${theme.palette.primary.main}`,
                            borderRadius: 4,
                            background: bg,
                            color,
                            outline: "none",
                            width: "100%",
                          }}
                        />
                      ) : (
                        <Tooltip title={t("common:renameColumn")} arrow>
                          <Typography
                            variant="body1"
                            onDoubleClick={() => handleStartEdit(field)}
                            sx={{
                              fontWeight: 600,
                              cursor: "pointer",
                              "&:hover": {
                                color: "primary.main",
                                textDecoration: "underline",
                              },
                            }}
                          >
                            {displayName}
                          </Typography>
                        </Tooltip>
                      )}

                      <Box
                        sx={{ display: "flex", alignItems: "center", gap: 1 }}
                      >
                        <ColumnTypeSelect
                          field={field}
                          value={columnType?.type}
                          disabled={editingColumn === field}
                          onChange={handleTypeChangeRequest}
                          bg={bg}
                          color={color}
                        />
                        <InferenceReasonPopover
                          columnName={displayName}
                          reason={columnType?.inference_reason}
                        />
                      </Box>

                      {columnType?.type === "Categorical" &&
                        columnType?.encoder && (
                          <EncoderChipBase
                            encoder={columnType.encoder}
                            encoderLabel={encoderLabel}
                            onSelect={(enc) =>
                              onEncoderChange && onEncoderChange(field, enc)
                            }
                          />
                        )}
                    </Box>
                  </th>
                );
              })}
            </tr>
          </thead>
          <tbody>
            {pageRows.map((row, rowIdx) => (
              <tr key={rowIdx}>
                {fields.map((field) => {
                  const val = row[field];
                  const isImage =
                    typeof val === "string" && val.startsWith("data:image");
                  return (
                    <td
                      key={field}
                      style={{
                        padding: "5px 12px",
                        fontSize: "0.875rem",
                        whiteSpace: "nowrap",
                        borderBottom: `1px solid ${divider}`,
                        verticalAlign: "middle",
                        maxWidth: 320,
                        overflow: "hidden",
                        textOverflow: "ellipsis",
                        color,
                      }}
                      title={isImage || val == null ? undefined : String(val)}
                    >
                      {isImage ? (
                        <img
                          src={val}
                          alt="img"
                          style={{
                            maxHeight: 48,
                            maxWidth: 48,
                            objectFit: "contain",
                          }}
                        />
                      ) : (
                        String(val ?? "")
                      )}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {rows?.length > PAGE_SIZE && (
        <TablePagination
          component="div"
          count={rows.length}
          page={page}
          rowsPerPage={PAGE_SIZE}
          rowsPerPageOptions={[PAGE_SIZE]}
          onPageChange={(_e, p) => setPage(p)}
          slotProps={{ select: { sx: { display: "none" } } }}
          labelRowsPerPage=""
          sx={{ fontSize: "0.8rem" }}
        />
      )}

      <TypeChangeValidator
        open={showValidator}
        onClose={handleCancelChanges}
        onConfirm={handleConfirmChanges}
        file={file}
        typeChanges={pendingChanges}
        params={params}
      />
    </>
  );
}

export default memo(PreviewDatasetTable);
