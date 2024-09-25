import React, { useCallback, useState, useEffect } from "react";
import { DataGrid } from "@mui/x-data-grid";
import { Grid, Typography } from "@mui/material";
import DeleteItemModal from "../custom/DeleteItemModal";
import ConverterEditorModal from "./ConverterEditorModal";
import PropTypes from "prop-types";
import ConverterScopeModal from "./ConverterScopeModal";
import { getDatasetInfo as getDatasetInfoRequest } from "../../api/datasets";
import { parseIndexToRange } from "../../utils/parseRange";
import ConverterPipelineModal from "./ConverterPipelineModal";

const ConverterTable = ({
  datasetId,
  convertersToApply,
  setConvertersToApply,
}) => {
  const [existingPipelines, setExistingPipelines] = useState([]);
  const [datasetInfo, setDatasetInfo] = useState({});
  const [loading, setLoading] = useState(true);

  const getDatasetInfo = async () => {
    setLoading(true);
    try {
      const datasetInfo = await getDatasetInfoRequest(datasetId);
      setDatasetInfo({ ...datasetInfo, id: datasetId });
    } catch (error) {
      enqueueSnackbar("Error while trying to obtain the dataset info.");
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

  useEffect(() => {
    getDatasetInfo();
  }, []);

  const updateOrder = (elementsToUpdate) => {
    const updatedElements = elementsToUpdate.map((element, index) => ({
      ...element,
      order: index + 1, // Update order
    }));
    return updatedElements;
  };

  const createDeleteHandler = useCallback(
    (id) => () => {
      let pipelines = [...existingPipelines];
      let converters = [...convertersToApply];
      let isPipeline = pipelines.some((pipeline) => pipeline.id === id);
      if (isPipeline) {
        // Delete pipeline and all its converters
        pipelines = pipelines.filter((pipeline) => pipeline.id !== id);

        converters = converters.filter(
          (converter) => converter.pipelineId !== id,
        );
      } else {
        // It is a converter
        let assignedPipelineId = converters.find(
          (converter) => converter.id === id,
        )?.pipelineId;
        // Check if the assigned pipeline is now empty and remove it from the list
        let pipelineToDelete = converters.filter(
          (converter) => converter.pipelineId === assignedPipelineId,
        );
        if (pipelineToDelete.length === 1) {
          pipelines = pipelines.filter(
            (pipeline) => pipeline.id !== assignedPipelineId,
          );
        }
        // Delete converter
        converters = converters.filter((converter) => converter.id !== id);
      }
      // Update order
      // setExistingPipelines(updateOrder(pipelines));
      // setConvertersToApply(updateOrder(converters));
      setExistingPipelines(pipelines);
      setConvertersToApply(converters);
    },
    [convertersToApply, existingPipelines],
  );

  const handleUpdateParams = (id) => (newParams) => {
    let updatedConverters = [...convertersToApply];
    let index = updatedConverters.findIndex((converter) => converter.id === id);
    if (index !== -1) {
      updatedConverters[index] = {
        ...updatedConverters[index],
        params: newParams,
      };

      setConvertersToApply(updatedConverters);
    }
  };

  const handleUpdateScope = (id) => (newScope) => {
    let index = convertersToApply.findIndex((converter) => converter.id === id);
    if (index !== -1) {
      let updatedConverters = [...convertersToApply];
      updatedConverters[index] = {
        ...updatedConverters[index],
        scope: newScope,
      };

      setConvertersToApply(updatedConverters);
      return;
    }
    let pipelineIndex = existingPipelines.findIndex(
      (pipeline) => pipeline.id === id,
    );
    if (pipelineIndex !== -1) {
      let updatedPipelines = [...existingPipelines];
      updatedPipelines[pipelineIndex] = {
        ...updatedPipelines[pipelineIndex],
        scope: newScope,
      };

      setExistingPipelines(updatedPipelines);
    }
  };

  const columns = React.useMemo(
    () => [
      {
        field: "order",
        headerName: "Order",
        minWidth: 50,
        editable: false,
        sortable: true,
      },
      {
        field: "name",
        headerName: "Converter",
        minWidth: 250,
        editable: false,
        sortable: false,
        renderCell: ({ row }) => {
          const inPipeline = row.pipelineId !== null;
          const isPipeline = existingPipelines.some(
            (pipeline) => pipeline.id === row.id,
          );
          return (
            <Grid container>
              <Grid item xs={12}>
                <Typography
                  style={
                    inPipeline && !isPipeline ? { marginLeft: "20px" } : {}
                  }
                >
                  {row.name}
                </Typography>
              </Grid>
            </Grid>
          );
        },
      },
      {
        field: `columns`,
        headerName: "Columns",
        minWidth: 100,
        editable: false,
        sortable: false,
        valueGetter: (params) => params.row.scope.columns,
        renderCell: ({ row }) => {
          const columns = row.scope.columns;
          const columnsLabel =
            columns.length > 0
              ? parseIndexToRange(columns).join(", ")
              : "All columns";
          const inPipeline = row.pipelineId !== null;
          const isPipeline = existingPipelines.some(
            (pipeline) => pipeline.id === row.id,
          );
          return (
            <Typography variant="p">
              {isPipeline || !inPipeline ? columnsLabel : ""}
            </Typography>
          );
        },
      },
      {
        field: `rows`,
        headerName: "Rows",
        minWidth: 100,
        editable: false,
        sortable: false,
        valueGetter: (params) => params.row.scope.rows,
        renderCell: ({ row }) => {
          const rows = row.scope.rows;
          const rowsLabel =
            rows.length > 0 ? parseIndexToRange(rows).join(", ") : "All rows";
          const inPipeline = row.pipelineId !== null;
          const isPipeline = existingPipelines.some(
            (pipeline) => pipeline.id === row.id,
          );
          return (
            <Typography variant="p">
              {isPipeline || !inPipeline ? rowsLabel : ""}
            </Typography>
          );
        },
      },
      {
        field: "actions",
        type: "actions",
        minWidth: 150,
        getActions: (params) =>
          [
            <ConverterEditorModal
              key="edit-component"
              converterToConfigure={params.row.name}
              updateParameters={handleUpdateParams(params.row.id)}
              paramsInitialValues={params.row.params}
            />,
            <ConverterScopeModal
              key="scope-component"
              elementToConfigure={params.row.name}
              updateScope={handleUpdateScope(params.row.id)}
              scopeInitialValues={params.row.scope}
              datasetInfo={datasetInfo}
            />,
            <ConverterPipelineModal
              key="pipeline-component"
              converters={convertersToApply}
              setConvertersToApply={setConvertersToApply}
              existingPipelines={existingPipelines}
              setExistingPipelines={setExistingPipelines}
              converterToAdd={params.row}
            />,
            <DeleteItemModal
              key="delete-component"
              deleteFromTable={createDeleteHandler(params.id)}
            />,
          ].filter((action) => {
            // Show all actions if the item is not in a pipeline
            if (params.row.pipelineId === null) {
              return true;
            }
            // Hide edit and pipeline components if the item is a pipeline
            let isPipeline = existingPipelines.some(
              (pipeline) => pipeline.id === params.row.id,
            );
            if (isPipeline) {
              return (
                action.key !== "edit-component" &&
                action.key !== "pipeline-component"
              );
            }
            // Hide scope component if the item is a converter in a pipeline
            return action.key !== "scope-component";
          }),
      },
    ],
    [createDeleteHandler],
  );

  // Rows include both pipelines and converters
  const rows = existingPipelines.reduce(
    (acc, pipeline) => {
      return [
        ...acc,
        pipeline,
        ...convertersToApply.filter(
          (converter) => converter.pipelineId === pipeline.id,
        ),
      ];
    },
    convertersToApply.filter((converter) => converter.pipelineId === null),
  );

  return (
    <Grid container>
      {/* Selected converters table */}
      <Grid item xs={12}>
        <DataGrid
          rows={rows}
          columns={columns}
          initialState={{
            sorting: {
              sortModel: [{ field: "order", sort: "asc" }],
            },
            pagination: {
              paginationModel: {
                pageSize: 5,
              },
            },
          }}
          pageSize={5}
          pageSizeOptions={[5, 10]}
          disableRowSelectionOnClick
          autoHeight
          loading={loading}
        />
      </Grid>
    </Grid>
  );
};

ConverterTable.propTypes = {
  convertersToApply: PropTypes.arrayOf(PropTypes.object),
  setConvertersToApply: PropTypes.func,
};

ConverterTable.defaultProps = {
  convertersToApply: [],
  setConvertersToApply: () => {},
};

export default ConverterTable;
