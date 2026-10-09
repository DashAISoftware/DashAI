import React, { useState, useEffect } from "react";
import {
  MaterialReactTable,
  useMaterialReactTable,
} from "material-react-table";
import PropTypes from "prop-types";
import {
  Box,
  IconButton,
  Typography,
  Button,
  Dialog,
  DialogContent,
  DialogTitle,
  DialogActions,
} from "@mui/material";
import { Close as CloseIcon, ViewColumn } from "@mui/icons-material";
import { getDatasetTypesByFilePath } from "../../../api/datasets";
import { useSnackbar } from "notistack";
import { useTranslation } from "react-i18next";
import { useTableLocalization } from "../../../utils/useTableLocalization";

/**
 * Modal to select a class column for supervised learning
 * @param {Object} props
 * @param {Function} props.updateClassColumn - Function to update the selected class column
 * @param {number} props.classColumnInitialValue - Initial value of the class column index
 * @param {number} props.notebook - notebook
 */
const ConverterTargetColumnModal = ({
  updateClassColumn,
  classColumnInitialValue = null,
  notebook,
}) => {
  const [open, setOpen] = useState(false);
  // rowSelection is an MRT selection map: { [rowId]: boolean }
  const [rowSelection, setRowSelection] = useState({});
  const [datasetColumns, setDatasetColumns] = useState([]);
  const [loading, setLoading] = useState(false);
  const { enqueueSnackbar } = useSnackbar();
  const { t } = useTranslation(["common", "datasets"]);
  const localization = useTableLocalization();

  const columns = [
    {
      accessorKey: "columnName",
      header: t("datasets:label.columnName"),
      grow: 1,
    },
    {
      accessorKey: "valueType",
      header: t("datasets:label.valueType"),
      grow: 0.5,
    },
    {
      accessorKey: "dataType",
      header: t("datasets:label.dataType"),
      grow: 0.5,
    },
  ];

  useEffect(() => {
    if (open) {
      // initialValue is 1-based column index; convert to 0-based row id
      if (classColumnInitialValue !== null) {
        const rowId = String(classColumnInitialValue - 1);
        setRowSelection({ [rowId]: true });
      } else {
        setRowSelection({});
      }
      fetchDatasetColumns();
    }
  }, [open, classColumnInitialValue]);

  const fetchDatasetColumns = async () => {
    setLoading(true);
    try {
      const types = await getDatasetTypesByFilePath(notebook.file_path);
      const rowsArray = Object.keys(types).map((name, idx) => ({
        id: idx,
        columnName: name,
        valueType: types[name].type,
        dataType: types[name].dtype,
      }));
      setDatasetColumns(rowsArray);
    } catch (error) {
      enqueueSnackbar(t("datasets:error.fetchingDatasetColumns"), {
        variant: "error",
      });
      if (error.response) {
        console.error("Response error:", error.message);
      } else if (error.request) {
        console.error("Request error", error.request);
      } else {
        console.error("Unknown Error", error.message);
      }
    } finally {
      setLoading(false);
    }
  };

  // Keep only the most recently selected row (single selection)
  const handleRowSelectionChange = (updaterOrValue) => {
    const newSelection =
      typeof updaterOrValue === "function"
        ? updaterOrValue(rowSelection)
        : updaterOrValue;

    // Enforce single selection: if more than one row is selected,
    // keep only the newly added one
    const prevKeys = Object.keys(rowSelection).filter((k) => rowSelection[k]);
    const newKeys = Object.keys(newSelection).filter((k) => newSelection[k]);
    const added = newKeys.find((k) => !prevKeys.includes(k));

    if (added !== undefined) {
      setRowSelection({ [added]: true });
    } else {
      setRowSelection(newSelection);
    }
  };

  const selectedRowId = Object.keys(rowSelection).find((k) => rowSelection[k]);

  const handleOnSave = () => {
    if (selectedRowId === undefined) {
      return;
    }
    const idx = parseInt(selectedRowId, 10);
    updateClassColumn(datasetColumns[idx]);
    setOpen(false);
  };

  const table = useMaterialReactTable({
    columns,
    data: datasetColumns,
    muiTableBodyCellProps: { sx: { whiteSpace: "pre" } },
    localization,
    initialState: {
      density: "compact",
      pagination: { pageSize: 25, pageIndex: 0 },
    },
    state: { rowSelection, isLoading: loading },
    onRowSelectionChange: handleRowSelectionChange,
    enableRowSelection: true,
    enableMultiRowSelection: false,
    enableGlobalFilter: true,
    getRowId: (row) => String(row.id),
  });

  return (
    <React.Fragment>
      <Button
        startIcon={<ViewColumn />}
        onClick={() => setOpen(true)}
        variant="outlined"
        size="small"
        sx={{
          color: classColumnInitialValue === null ? "error.main" : "inherit",
          borderColor:
            classColumnInitialValue === null ? "error.main" : "inherit",
          "&:hover": {
            borderColor:
              classColumnInitialValue === null ? "error.main" : "inherit",
            backgroundColor:
              classColumnInitialValue === null ? "error.light" : "inherit",
          },
        }}
      >
        {t("datasets:button.setColumn")}
      </Button>
      {open && (
        <Dialog
          open={open}
          onClose={() => setOpen(false)}
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
          <DialogTitle sx={{ bgcolor: "background.paper" }}>
            <Box
              sx={{
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
              }}
            >
              {t("datasets:button.setColumn")}
              <IconButton
                onClick={() => setOpen(false)}
                size="small"
                sx={{ color: "text.secondary" }}
              >
                <CloseIcon />
              </IconButton>
            </Box>
          </DialogTitle>

          <DialogContent dividers sx={{ bgcolor: "background.paper" }}>
            <Box>
              <Typography variant="h6" sx={{ mb: 2 }}>
                {t("datasets:label.classTargetColumn")}
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 4 }}>
                {t("datasets:label.selectTargetColumnDescription")}
              </Typography>
              <MaterialReactTable table={table} />
            </Box>
          </DialogContent>

          <DialogActions sx={{ p: 4, bgcolor: "background.paper" }}>
            <Button variant="outlined" onClick={() => setOpen(false)}>
              {t("common:back")}
            </Button>
            <Button
              variant="contained"
              onClick={handleOnSave}
              disabled={selectedRowId === undefined}
            >
              {t("common:save")}
            </Button>
          </DialogActions>
        </Dialog>
      )}
    </React.Fragment>
  );
};

ConverterTargetColumnModal.propTypes = {
  updateClassColumn: PropTypes.func.isRequired,
  classColumnInitialValue: PropTypes.number,
  notebook: PropTypes.shape({
    file_path: PropTypes.string,
  }).isRequired,
};

export default ConverterTargetColumnModal;
