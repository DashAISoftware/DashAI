import React, { useEffect, useState } from "react";
import PropTypes from "prop-types";
import {
  GridActionsCellItem,
  DataGrid,
  useGridApiContext,
} from "@mui/x-data-grid";
import {
  getDatasetSample as getDatasetSampleRequest,
  getDatasetTypes as getDatasetTypesRequest,
} from "../../api/datasets";
import SearchIcon from "@mui/icons-material/Search";
import {
  Dialog,
  DialogContent,
  DialogTitle,
  Grid,
  Typography,
} from "@mui/material";
import { useSnackbar } from "notistack";
import { dataTypesList, columnTypesList } from "../../utils/typesLists";
import SelectTypeCell from "../custom/SelectTypeCell";

/**
 * This component renders a view to look up the dataset with a summary,
 * and in next updates with relevant information about the dataset.
 */
function DatasetLookup({
  uploadedDataset,
  setNextEnabled,
  datasetUploaded,
  columnsSpec,
  setColumnsSpec,
}) {
  const { enqueueSnackbar } = useSnackbar();
  const [open, setOpen] = useState(false);
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(true);

  const getDatasetInfo = async () => {
    setLoading(true);
    try {
      const dataset = await getDatasetSampleRequest(uploadedDataset.id);
      const types = await getDatasetTypesRequest(uploadedDataset.id);
      const rowsArray = Object.keys(dataset).map((name, idx) => {
        return {
          id: idx,
          columnName: name,
          example: dataset[name][0],
          columnType: types[name].type,
          dataType: types[name].dtype,
        };
      });
      setRows(rowsArray);
      setColumnsSpec(types);
    } catch (error) {
      enqueueSnackbar("Error while trying to obtain the dataset.");
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

  const updateCellValue = async (id, field, newValue) => {
    const apiRef = useGridApiContext();
    await apiRef.current.setEditCellValue({ id, field, value: newValue });
    apiRef.current.stopCellEditMode({ id, field });

    setRows((prevRows) =>
      prevRows.map((row) =>
        row.id === id ? { ...row, [field]: newValue } : row,
      ),
    );

    const columnName = rows.find((row) => row.id === id)?.columnName;
    const updateColumns = { ...columnsSpec };

    if (field === "dataType") {
      updateColumns[columnName].dtype = newValue;
    } else if (field === "columnType") {
      updateColumns[columnName].type = newValue;
    }

    setColumnsSpec(updateColumns);
  };

  const renderSelectCell = (params, options) => {
    return (
      <SelectTypeCell
        id={params.id}
        value={params.value}
        field={params.field}
        options={options}
        updateValue={updateCellValue}
      />
    );
  };

  const columns = [
    {
      field: "columnName",
      headerName: "Column name",
      minWidth: 200,
      editable: false,
    },
    {
      field: "example",
      headerName: "Example",
      minWidth: 200,
      editable: false,
    },
    {
      field: "columnType",
      headerName: "Column type",
      renderEditCell: (params) => renderSelectCell(params, columnTypesList),
      minWidth: 200,
      editable: true,
    },
    {
      field: "dataType",
      headerName: "Data type",
      renderEditCell: (params) => renderSelectCell(params, dataTypesList),
      minWidth: 200,
      editable: true,
    },
  ];

  useEffect(() => {
    if (datasetUploaded) {
      getDatasetInfo();
      setNextEnabled(true);
    }
  }, [datasetUploaded]);

  return (
    <React.Fragment>
      <GridActionsCellItem
        key="convert-button"
        icon={<SearchIcon />}
        label="Convert"
        onClick={() => [setOpen(true), getDatasetInfo()]}
        sx={{ color: "text.primary" }}
      />
      <Dialog
        open={open}
        onClose={() => setOpen(false)}
        fullWidth
        maxWidth={"md"}
      >
        <DialogTitle>
          <Grid container direction={"row"} alignItems={"center"}>
            <Grid item xs={12} md={3}>
              <Typography
                variant="h6"
                component={"h3"}
                sx={{ mb: { sm: 2, md: 0 } }}
              >
                Data Lookup
              </Typography>
            </Grid>
          </Grid>
        </DialogTitle>
        <DialogContent dividers>
          <Grid
            container
            direction="row"
            justifyContent="space-around"
            alignItems="stretch"
            spacing={2}
          >
            <Grid item xs={12}>
              <Typography variant="subtitle1" component="h3">
                Look up the Dataset Summary and relevant information about the
                dataset.
              </Typography>
            </Grid>

            {/* Form to add a converter to the dataset */}
            <Grid item xs={12}>
              <Grid
                container
                direction="row"
                columnSpacing={3}
                wrap="nowrap"
                justifyContent="flex-start"
              ></Grid>
            </Grid>

            {/* Models table */}
            <Grid item xs={12}>
              <Typography variant="subtitle1" component="h3">
                {/* Datasets Table */}
                <DataGrid
                  rows={rows}
                  columns={columns}
                  initialState={{
                    pagination: {
                      paginationModel: {
                        pageSize: 5,
                      },
                    },
                  }}
                  pageSize={5}
                  pageSizeOptions={[5, 10]}
                  loading={loading}
                  disableRowSelectionOnClick
                  autoHeight
                />
              </Typography>
            </Grid>
          </Grid>
        </DialogContent>
      </Dialog>
    </React.Fragment>
  );
}

DatasetLookup.propTypes = {
  datasetId: PropTypes.number.isRequired,
  name: PropTypes.string.isRequired,
  setNextEnabled: PropTypes.func.isRequired,
  uploadedDataset: PropTypes.object,
  datasetUploaded: PropTypes.bool,
  columnsSpec: PropTypes.object.isRequired,
  setColumnsSpec: PropTypes.func.isRequired,
};

export default DatasetLookup;
