import React, { useEffect, useMemo, useState } from "react";
import PropTypes from "prop-types";
import { refusedDtypes as refusedDtypesOf } from "../../../utils/columnEligibility";

import {
  Dialog,
  DialogContent,
  DialogTitle,
  Box,
  IconButton,
  Typography,
  Chip,
  Stack,
} from "@mui/material";
import { ArrowBackOutlined, ViewColumn } from "@mui/icons-material";
import {
  MaterialReactTable,
  useMaterialReactTable,
} from "material-react-table";
import { useTheme } from "@mui/material/styles";
import { useTableLocalization } from "../../../utils/useTableLocalization";

import TooltipedCellItem from "../../shared/TooltipedCellItem";

import { useSnackbar } from "notistack";

// Convert array of IDs → MRT rowSelection format { [id]: boolean }
const toMRT = (ids) => Object.fromEntries(ids.map((id) => [String(id), true]));
// Convert MRT rowSelection → array of numeric IDs
const fromMRT = (sel) =>
  Object.keys(sel)
    .filter((k) => sel[k])
    .map(Number);

const columnDefs = [
  {
    accessorKey: "id",
    header: "Index",
    size: 80,
  },
  {
    accessorKey: "columnName",
    header: "Column Name",
    grow: true,
  },
  {
    accessorKey: "valueType",
    header: "Value Type",
    size: 120,
  },
  {
    accessorKey: "dataType",
    header: "Data Type",
    size: 120,
  },
  {
    accessorKey: "order",
    header: "Selected Order",
    size: 130,
  },
];

/**
 * Dialog to edit columns selection
 * @param {Object} props
 * @param {Array} props.datasetColumns List of columns
 * @param {Function} props.updateValue Callback to update the selected columns
 * @param {Array} props.initialValues Initial selected columns
 * @param {Object} props.explorerType Explorer type object with metadata
 */
function EditColumnsDialog({
  datasetColumns,
  updateValue,
  initialValues,
  explorerType,
}) {
  const { enqueueSnackbar } = useSnackbar();
  const theme = useTheme();
  const localization = useTableLocalization();

  const [open, setOpen] = useState(false);
  const handleClose = () => {
    if (!isValidSelection(fromMRT(rowSelection))) {
      enqueueSnackbar("Invalid selection, changes were not be saved", {
        variant: "warning",
      });
    }
    setOpen(false);
  };

  const explorer = explorerType?.value;
  const allowedDtypes = explorer?.metadata?.allowed_dtypes || [];
  // The backend renamed this key to non_allowed_dtypes and pops the old one, so
  // the "does not accept" chips below never rendered: the user was never told
  // about a blacklist that the backend does enforce.
  const refusedDtypes = refusedDtypesOf(explorer?.metadata);
  const inputCardinality = explorer?.metadata?.input_cardinality || {};
  const validColumns = explorerType?.validColumns || [];

  const [rows, setRows] = useState([]);
  useEffect(() => {
    if (datasetColumns) {
      const validColsId = new Set(validColumns.map((col) => col.id));
      const cols = datasetColumns.map((col) => {
        return {
          ...col,
          disabled: !validColsId.has(col.id),
          order: initialValues.find((row) => row.id === col.id)?.order || 0,
        };
      });
      setRows(cols);
    }
  }, [datasetColumns, explorerType, open]);

  // rowSelection in MRT format: { [id]: boolean }
  const [rowSelection, setRowSelection] = useState({});

  // update row selection on initial values change or dialog open
  useEffect(() => {
    setRowSelection(toMRT(initialValues.map((params) => params.id)));
  }, [initialValues, open]);

  const handleSelectionChange = (updaterOrValue) => {
    const newMrtSelection =
      typeof updaterOrValue === "function"
        ? updaterOrValue(rowSelection)
        : updaterOrValue;

    // Convert to array of numeric IDs in selection order
    let selectedIds = fromMRT(newMrtSelection);

    if (selectedIds.length > inputCardinality.max) {
      selectedIds = selectedIds.slice(0, inputCardinality.max);
    }

    // Rebuild MRT selection from potentially truncated list
    const finalMrtSelection = toMRT(selectedIds);

    // Update order for the rows
    let newRows = rows.map((row) => {
      const order = selectedIds.indexOf(row.id) + 1;
      return { ...row, order };
    });
    setRows(newRows);
    setRowSelection(finalMrtSelection);

    if (!isValidSelection(selectedIds)) return;

    updateValue(
      newRows
        .filter((row) => selectedIds.includes(row.id))
        .sort((a, b) => a.order - b.order)
        .map((row) => ({
          id: row.id,
          columnName: row.columnName,
          valueType: row.valueType,
          dataType: row.dataType,
          order: row.order,
        })),
    );
  };

  const isRowSelectable = (row) => {
    const id = row.original.id;

    // Already selected rows remain selectable
    if (rowSelection[String(id)]) {
      return true;
    }

    // Disabled rows are not selectable
    if (row.original.disabled) {
      return false;
    }

    // Max cardinality reached
    const selectedCount = fromMRT(rowSelection).length;
    const maxReached =
      selectedCount >= inputCardinality.max ||
      selectedCount >= inputCardinality.exact;
    if (maxReached) {
      return false;
    }

    return true;
  };

  const isValidSelection = (selection) => {
    if (inputCardinality.exact && selection.length !== inputCardinality.exact) {
      return false;
    }
    if (inputCardinality.min && selection.length < inputCardinality.min) {
      return false;
    }
    if (inputCardinality.max && selection.length > inputCardinality.max) {
      return false;
    }
    return true;
  };

  const columns = useMemo(() => columnDefs, []);

  const table = useMaterialReactTable({
    columns,
    data: rows,
    muiTableBodyCellProps: { sx: { whiteSpace: "pre" } },
    getRowId: (row) => String(row.id),
    enableRowSelection: isRowSelectable,
    onRowSelectionChange: handleSelectionChange,
    state: { rowSelection },
    enableGlobalFilter: true,
    enableColumnFilters: false,
    enableSorting: true,
    enableDensityToggle: false,
    enableFullScreenToggle: false,
    enableHiding: false,
    autoResetPageIndex: false,
    initialState: {
      density: "compact",
      pagination: { pageIndex: 0, pageSize: 5 },
    },
    muiTableBodyRowProps: ({ row }) => ({
      sx:
        !isRowSelectable(row) && !rowSelection[String(row.original.id)]
          ? {
              backgroundColor: "rgba(0, 0, 0, 0.12)",
              color: "#777",
            }
          : {},
    }),
    localization,
  });

  return (
    <React.Fragment>
      <TooltipedCellItem
        key="edit-columns-button"
        icon={<ViewColumn />}
        label="Edit Columns"
        tooltip={`Edit column selection`}
        onClick={() => setOpen(true)}
      />
      {open && (
        <Dialog
          open={open}
          onClose={handleClose}
          slotProps={{
            paper: {
              sx: {
                width: { md: 820, lg: 1000 },
                maxHeight: { lg: 700, xl: "auto" },
                maxWidth: 2000,
                transition: "width 0.3s ease, height 0.3s ease",
              },
            },
          }}
        >
          <DialogTitle>
            <Box display="flex" alignItems="center">
              <IconButton onClick={handleClose}>
                <ArrowBackOutlined />
              </IconButton>
              <Typography variant="h5" sx={{ ml: 4 }}>
                Update Column Selection
              </Typography>
            </Box>
          </DialogTitle>
          <DialogContent>
            <Box sx={{ height: "100%", width: "100%" }}>
              <Typography
                variant="body1"
                sx={{ mb: 4, whiteSpace: "pre-line" }}
              >
                {`Select the columns you want to use for the ${explorerType.label} exploration`}
              </Typography>

              <Stack
                direction="row"
                spacing={2}
                sx={{ mb: 2, display: "flex", justifyContent: "space-evenly" }}
              >
                {inputCardinality.min && (
                  <Typography variant="body2">
                    Minimum number of columns: {inputCardinality.min}
                  </Typography>
                )}
                {inputCardinality.exact && (
                  <Typography variant="body2">
                    Number of columns required: {inputCardinality.exact}
                  </Typography>
                )}
                {inputCardinality.max && (
                  <Typography variant="body2">
                    Maximum number of columns: {inputCardinality.max}
                  </Typography>
                )}
              </Stack>

              {allowedDtypes.length > 0 && (
                <Box
                  sx={{
                    mb: 2,
                    display: "flex",
                    flexDirection: "row",
                    gap: 2,
                    alignItems: "center",
                  }}
                >
                  <Typography variant="body2">Allowed data types:</Typography>
                  {allowedDtypes.map((dtype) => (
                    <Chip
                      key={dtype}
                      label={dtype}
                      color="secondary"
                      size="small"
                    />
                  ))}
                </Box>
              )}
              {refusedDtypes.length > 0 && (
                <Box
                  sx={{
                    mb: 2,
                    display: "flex",
                    flexDirection: "row",
                    gap: 2,
                    alignItems: "center",
                  }}
                >
                  <Typography variant="body2">
                    Restricted data types:
                  </Typography>
                  {refusedDtypes.map((dtype) => (
                    <Chip
                      key={dtype}
                      label={dtype}
                      color="error"
                      size="small"
                    />
                  ))}
                </Box>
              )}

              <MaterialReactTable table={table} />
            </Box>
          </DialogContent>
        </Dialog>
      )}
    </React.Fragment>
  );
}

EditColumnsDialog.propTypes = {
  datasetColumns: PropTypes.array.isRequired,
  updateValue: PropTypes.func.isRequired,
  initialValues: PropTypes.array.isRequired,
  explorerType: PropTypes.object.isRequired,
};

export default EditColumnsDialog;
