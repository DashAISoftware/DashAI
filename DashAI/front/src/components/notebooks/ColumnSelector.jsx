import { useState, useEffect, useCallback, useMemo } from "react";
import PropTypes from "prop-types";
import { Alert, Box, Typography } from "@mui/material";
import {
  MaterialReactTable,
  useMaterialReactTable,
} from "material-react-table";
import { useTheme } from "@mui/material/styles";
import { getDatasetTypesByFilePath } from "../../api/datasets";
import { Trans, useTranslation } from "react-i18next";
import { useTableLocalization } from "../../utils/useTableLocalization";

/**
 * Generic column selection component that can be reused across the application
 *
 * Features:
 * - Configurable cardinality constraints (min, max, exact)
 * - Data type filtering (allowed/restricted)
 * - Automatic selection based on cardinality rules
 * - Visual feedback for invalid/disabled columns
 * - Customizable grid columns and styling
 * - Validation callbacks for real-time feedback
 *
 * Usage:
 * - Any component requiring column selection with constraints
 *
 * @param {Object} props
 * @param {Array} props.file_path - String path to the dataset file
 * @param {Object} props.inputCardinality - Cardinality requirements {min, max, exact} (optional)
 * @param {Array} props.allowedDtypes - Array of allowed dtype strings (optional)
 * @param {Array} props.allowedTypes - Array of allowed semantic type names (optional)
 * @param {Array} props.nonAllowedDtypes - Array of forbidden dtype strings (optional)
 * @param {Array} props.excludedColumnIds - Array of row ids that cannot be selected regardless of type (optional)
 * @param {Function} props.onSelectionChange - Callback when selection changes (selectedColumns) (optional)
 * @param {Function} props.onValidationChange - Callback when validation status changes (isValid) (optional)

 */
function ColumnSelector({
  file_path,
  tool,
  inputCardinality = {},
  allowedDtypes = [],
  allowedTypes = [],
  nonAllowedDtypes = [],
  excludedColumnIds = [],
  onSelectionChange = () => {},
  onValidationChange = () => {},
  columnTypes = null,
}) {
  const [rows, setRows] = useState([]);
  const [rowSelectionModel, setRowSelectionModel] = useState([]);
  const [datasetColumns, setDatasetColumns] = useState([]);
  const { t } = useTranslation(["datasets", "common"]);
  const theme = useTheme();
  const localization = useTableLocalization();

  const toMRT = (ids) =>
    Object.fromEntries(ids.map((id) => [String(id), true]));
  const fromMRT = (sel) =>
    Object.keys(sel)
      .filter((k) => sel[k])
      .map(Number);

  const columns = useMemo(
    () => [
      {
        accessorKey: "id",
        header: t("common:index"),
        size: 60,
      },
      {
        accessorKey: "columnName",
        header: t("datasets:label.columnName"),
        flex: 1,
      },
      {
        accessorKey: "valueType",
        header: t("datasets:label.valueType"),
        flex: 0.5,
      },
      {
        accessorKey: "dataType",
        header: t("datasets:label.dataType"),
        flex: 0.5,
      },
      {
        accessorKey: "order",
        header: t("datasets:label.selectedOrder"),
        flex: 0.5,
      },
    ],
    [t],
  );

  useEffect(() => {
    const toColumns = (types) =>
      Object.entries(types).map(([columnName, typeInfo], idx) => ({
        id: idx,
        columnName: columnName,
        valueType: typeInfo.type || t("common:unknown"),
        dataType: typeInfo.dtype || t("common:unknown"),
        order: idx,
      }));

    if (columnTypes !== null) {
      const cols = toColumns(columnTypes);
      setDatasetColumns(cols);
      setRows(cols);
      return;
    }

    let isMounted = true;
    const fetchAllData = async () => {
      try {
        const types = await getDatasetTypesByFilePath(file_path);
        if (!isMounted) return;
        const cols = toColumns(types);
        setDatasetColumns(cols);
        setRows(cols);
      } catch (error) {
        console.error("Error fetching dataset info/types:", error);
      }
    };

    fetchAllData();

    return () => {
      isMounted = false;
    };
  }, [file_path, columnTypes]);

  // Validate current selection
  const isValidSelection = useCallback(
    (selection) => {
      if (selection.length === 0) {
        return false;
      }

      if (
        inputCardinality.exact &&
        selection.length !== inputCardinality.exact
      ) {
        return false;
      }

      if (inputCardinality.min && selection.length < inputCardinality.min) {
        return false;
      }

      if (inputCardinality.max && selection.length > inputCardinality.max) {
        return false;
      }

      return true;
    },
    [inputCardinality],
  );
  const getValidColumnIds = useCallback(() => {
    return rows
      .filter((row) => {
        if (excludedColumnIds.includes(row.id)) {
          return false;
        }
        if (allowedTypes.length > 0 && !allowedTypes.includes(row.valueType)) {
          return false;
        }
        if (allowedDtypes.length > 0 && !allowedDtypes.includes(row.dataType)) {
          return false;
        }
        if (nonAllowedDtypes.length > 0) {
          const dtypeKey =
            row.dataType === t("common:unknown") ? "" : row.dataType;
          if (nonAllowedDtypes.includes(dtypeKey)) return false;
        }
        return true;
      })
      .map((row) => row.id);
  }, [rows, allowedDtypes, allowedTypes, nonAllowedDtypes, excludedColumnIds]);

  // Deselect any already-selected column that becomes excluded (e.g. it was
  // picked as scope and then also set as the target column)
  useEffect(() => {
    if (excludedColumnIds.length === 0) return;
    const filtered = rowSelectionModel.filter(
      (id) => !excludedColumnIds.includes(id),
    );
    if (filtered.length === rowSelectionModel.length) return;
    setRowSelectionModel(filtered);
    setRows((prevRows) =>
      prevRows.map((row) => ({
        ...row,
        order: filtered.indexOf(row.id) + 1,
      })),
    );
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [excludedColumnIds, rowSelectionModel]);

  // Check if row is selectable - using useCallback for stability
  const isRowSelectable = useCallback(
    (params) => {
      const validIds = getValidColumnIds();
      const isColumnValid = validIds.includes(params.id);

      if (!isColumnValid) {
        return false;
      }

      const selectedCount = rowSelectionModel.length;
      const isAlreadySelected = rowSelectionModel.includes(params.id);

      // If already selected, always allow deselection
      if (isAlreadySelected) {
        return true;
      }

      // Check exact cardinality constraint
      if (inputCardinality.exact && selectedCount >= inputCardinality.exact) {
        return false;
      }

      // Check max cardinality constraint
      if (inputCardinality.max && selectedCount >= inputCardinality.max) {
        return false;
      }

      return true;
    },
    [getValidColumnIds, rowSelectionModel, inputCardinality],
  );

  const handleSelectAllRows = useCallback(() => {
    const limit = inputCardinality.exact || inputCardinality.max;
    const validIds = getValidColumnIds();
    const selectableIds = limit ? validIds.slice(0, limit) : validIds;
    const allSelectableSelected =
      selectableIds.length > 0 &&
      selectableIds.every((id) => rowSelectionModel.includes(id));

    handleSelection(allSelectableSelected ? {} : toMRT(selectableIds));
  }, [getValidColumnIds, rowSelectionModel, inputCardinality]);

  // Effect to update selection data and validation whenever rowSelectionModel changes
  useEffect(() => {
    if (rows.length > 0) {
      const selectedColumnsData = rowSelectionModel
        .map((selectedId, index) => {
          const row = rows.find((r) => r.id === selectedId);
          return row
            ? {
                ...row,
                order: index + 1,
              }
            : null;
        })
        .filter(Boolean);

      onSelectionChange(selectedColumnsData);

      const isValid = isValidSelection(rowSelectionModel);
      onValidationChange(isValid);
    }
  }, [
    rowSelectionModel,
    rows,
    isValidSelection,
    onSelectionChange,
    onValidationChange,
  ]);

  const handleSelection = (updaterOrValue) => {
    const newMRTSelection =
      typeof updaterOrValue === "function"
        ? updaterOrValue(toMRT(rowSelectionModel))
        : updaterOrValue;
    let selection = fromMRT(newMRTSelection);
    if (inputCardinality.max && selection.length > inputCardinality.max) {
      selection = selection.slice(0, inputCardinality.max);
    }
    const newRows = rows.map((row) => {
      const order = selection.indexOf(row.id) + 1;
      return { ...row, order };
    });

    setRows(newRows);
    setRowSelectionModel(selection);
  };

  const isTypeInvalid = useCallback(
    (rowId) => !getValidColumnIds().includes(rowId),
    [getValidColumnIds],
  );

  const columnSelectorTable = useMaterialReactTable({
    columns,
    data: rows,
    muiTableBodyCellProps: ({ row }) => ({
      sx: {
        whiteSpace: "pre",
        ...(isTypeInvalid(row.original.id) && {
          color: theme.palette.text.disabled,
          textDecoration: "line-through",
          textDecorationColor: theme.palette.text.disabled,
        }),
      },
    }),
    enableRowSelection: (row) => isRowSelectable({ id: row.original.id }),
    onRowSelectionChange: handleSelection,
    state: { rowSelection: toMRT(rowSelectionModel) },
    getRowId: (row) => String(row.id),
    enableGlobalFilter: true,
    enableColumnFilters: false,
    enableColumnActions: false,
    enableSorting: false,
    enableDensityToggle: false,
    enableFullScreenToggle: false,
    enableHiding: false,
    enablePagination: true,
    autoResetPageIndex: false,
    muiPaginationProps: { rowsPerPageOptions: [10, 15, 20] },
    initialState: {
      pagination: { pageSize: 10, pageIndex: 0 },
      density: "compact",
    },
    mrtTheme: {
      baseBackgroundColor: theme.palette.ui.panelDark,
    },
    muiTablePaperProps: {
      elevation: 0,
      sx: { border: "1px solid", borderColor: "divider" },
    },
    muiTableBodyRowProps: ({ row }) => ({
      sx: isTypeInvalid(row.original.id)
        ? {
            backgroundColor: theme.palette.ui.rowDisabled,
            opacity: 0.55,
            cursor: "not-allowed",
            pointerEvents: "none",
          }
        : {},
    }),
    muiSelectAllCheckboxProps: () => {
      const limit = inputCardinality.exact || inputCardinality.max;
      const validIds = getValidColumnIds();
      const selectableIds = limit ? validIds.slice(0, limit) : validIds;
      return {
        checked:
          selectableIds.length > 0 &&
          selectableIds.every((id) => rowSelectionModel.includes(id)),
        indeterminate:
          rowSelectionModel.length > 0 &&
          rowSelectionModel.length < selectableIds.length,
        onChange: handleSelectAllRows,
      };
    },
    localization,
  });

  const valid = isValidSelection(rowSelectionModel);

  return (
    <Box>
      {/* Column requirements */}
      <Box
        sx={{
          mb: 3,
          p: 3,
          borderRadius: 2,
          backgroundColor: theme.palette.ui.hover,
          border: `1px solid ${theme.palette.ui.divider}`,
          textAlign: "center",
        }}
      >
        {Object.keys(inputCardinality).length > 0 && (
          <Typography variant="body2" sx={{ color: "text.secondary", mb: 1 }}>
            {t("datasets:label.requiredColumns", {
              exact: inputCardinality.exact,
              min: inputCardinality.min || 0,
              max: inputCardinality.max,
              context: inputCardinality.exact
                ? "exact"
                : inputCardinality.max
                  ? "range"
                  : "min",
            })}
          </Typography>
        )}

        <Typography
          variant="body2"
          sx={{
            fontWeight: 700,
            color: valid ? "success.main" : "error.main",
            letterSpacing: 0.3,
            mb: allowedTypes.length > 0 || allowedDtypes.length > 0 ? 1 : 0,
          }}
        >
          {t("datasets:label.selectedColumns", {
            count: rowSelectionModel.length,
          })}{" "}
          {valid ? "✓" : ""}
        </Typography>

        {/* Allowed value types (semantic) */}
        {allowedTypes.length > 0 && (
          <Typography
            variant="body2"
            sx={{
              color: "text.secondary",
              fontStyle: "italic",
              mt: 2,
            }}
          >
            <Trans i18nKey="datasets:label.allowedValueTypes">
              Allowed types:
              <Box
                component="span"
                sx={{ color: "secondary.main", fontWeight: 500 }}
              >
                {allowedTypes.join(", ")}
              </Box>
            </Trans>
          </Typography>
        )}
        {/* Allowed data types */}
        {allowedDtypes.length > 0 && (
          <Typography
            variant="caption"
            sx={{ color: "text.disabled", mt: 1, display: "block" }}
          >
            {t("common:allowedTypes")}:{" "}
            <Box
              component="span"
              sx={{ color: "secondary.main", fontWeight: 500 }}
            >
              {allowedDtypes.join(", ")}
            </Box>
          </Typography>
        )}

        {/* Excluded data types */}
        {nonAllowedDtypes.length > 0 && (
          <Typography
            variant="caption"
            sx={{ color: "warning.main", mt: 1, display: "block" }}
          >
            {t("datasets:label.excludedDataTypes", {
              dtypes: nonAllowedDtypes
                .map((d) => (d === "" ? t("common:unknown") : d))
                .join(", "),
            })}
          </Typography>
        )}
      </Box>

      {tool?.metadata?.changes_row_count && (
        <Alert
          severity="warning"
          sx={{
            "& .MuiAlert-icon": { fontSize: 24 },
            bgcolor: (theme) => `${theme.palette.warning.main}40`,
            border: (theme) => `1px solid ${theme.palette.warning.main}`,
            "& \t.MuiAlert-message": {
              display: "flex",
              alignItems: "center",
            },
            mb: 1.5,
          }}
        >
          {t("datasets:message.changesRowCountWarning")}
        </Alert>
      )}

      {/* Data Grid */}
      <Box data-tour="column-selector">
        <MaterialReactTable table={columnSelectorTable} />
      </Box>
    </Box>
  );
}

ColumnSelector.propTypes = {
  file_path: PropTypes.string.isRequired,
  tool: PropTypes.shape({
    metadata: PropTypes.shape({
      changes_row_count: PropTypes.bool,
    }),
  }),
  inputCardinality: PropTypes.shape({
    min: PropTypes.number,
    max: PropTypes.number,
    exact: PropTypes.number,
  }),
  allowedDtypes: PropTypes.array,
  allowedTypes: PropTypes.array,
  nonAllowedDtypes: PropTypes.array,
  excludedColumnIds: PropTypes.array,
  onSelectionChange: PropTypes.func,
  onValidationChange: PropTypes.func,
};

export default ColumnSelector;
