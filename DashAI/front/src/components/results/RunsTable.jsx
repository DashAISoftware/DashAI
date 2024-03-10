// import React, { useEffect, useState } from "react";
// import PropTypes from "prop-types";
// import { Alert, AlertTitle, CircularProgress, Paper } from "@mui/material";
// import { DataGrid, GridActionsCellItem, GridToolbar } from "@mui/x-data-grid";
// import { getRuns as getRunsRequest } from "../../api/run";
// import { getComponents as getComponentsRequest } from "../../api/component";
// import { getExperimentById } from "../../api/experiment";
// import { useSnackbar } from "notistack";
// import { useNavigate } from "react-router-dom";
// import QueryStatsIcon from "@mui/icons-material/QueryStats";
// import { getRunStatus } from "../../utils/runStatus";
// import { formatDate } from "../../utils/index";

// // columns that are common to all runs
// const initialColumns = [
//   {
//     field: "name",
//     headerName: "Name",
//     minWidth: 150,
//   },
//   {
//     field: "model_name",
//     headerName: "Model",
//     minWidth: 150,
//   },
//   {
//     field: "status",
//     headerName: "Status",
//     minWidth: 150,
//   },
//   {
//     field: "created",
//     headerName: "Created",
//     type: Date,
//     minWidth: 140,
//     valueFormatter: (params) => formatDate(params.value),
//   },
//   {
//     field: "last_modified",
//     headerName: "Last modified",
//     type: Date,
//     minWidth: 140,
//     valueFormatter: (params) => formatDate(params.value),
//   },
//   {
//     field: "start_time",
//     headerName: "Start",
//     type: Date,
//     minWidth: 140,
//     valueFormatter: (params) => formatDate(params.value),
//   },
//   {
//     field: "end_time",
//     headerName: "End",
//     type: Date,
//     minWidth: 140,
//     valueFormatter: (params) => formatDate(params.value),
//   },
// ];

// // name of the properties in the run object that contain objects
// const runObjectProperties = [
//   "train_metrics",
//   "test_metrics",
//   "validation_metrics",
//   "parameters",
// ];

// // function to get prefixes for the column names of each metric
// const getPrefix = (property) => {
//   switch (property) {
//     case "train_metrics":
//       return "train_";
//     case "test_metrics":
//       return "test_";
//     case "validation_metrics":
//       return "val_";
//     default:
//       return "";
//   }
// };
// /**
//  * This component renders a table that contains the runs associated to an experiment.
//  * @param {string} experimentId id of the experiment whose runs the user wants to analyze.
//  */
// function RunsTable({ experimentId }) {
//   const { enqueueSnackbar } = useSnackbar();
//   const navigate = useNavigate();

//   const [rows, setRows] = useState([]);
//   const [columns, setColumns] = useState([]);
//   const [columnGroupingModel, setColumnGroupingModel] = useState([]);
//   const [columnVisibilityModel, setColumnVisibilityModel] = useState({});
//   const [loading, setLoading] = useState(false);

//   const actionsColumns = [
//     {
//       field: "actions",
//       type: "actions",
//       minWidth: 80,
//       getActions: (params) => [
//         <GridActionsCellItem
//           key="specific-results-button"
//           icon={<QueryStatsIcon />}
//           label="Run Results"
//           onClick={() =>
//             navigate(
//               `/app/results/experiments/${experimentId}/runs/${params.id}`,
//             )
//           }
//           sx={{ color: "primary.main" }}
//         />,
//       ],
//     },
//   ];

//   const extractRows = (rawRuns) => {
//     let rows = [];
//     rawRuns.forEach((run) => {
//       let newRun = { ...run };
//       runObjectProperties.forEach((p) => {
//         // adds its corresponding prefix to the metric name (e.g. train_F1) and
//         // if the metric value is a number, it is rounded to two decimal places.
//         Object.keys(run[p] ?? {}).forEach((metric) => {
//           newRun = {
//             ...newRun,
//             [`${getPrefix(p)}${metric}`]:
//               typeof run[p][metric] === "number"
//                 ? run[p][metric].toFixed(2)
//                 : run[p][metric],
//           };
//         });
//       });
//       rows = [...rows, newRun];
//     });
//     return rows;
//   };

//   const extractColumns = (rawMetrics, rawRuns) => {
//     // extract metrics
//     let metrics = [];
//     for (const metric of rawMetrics) {
//       metrics = [
//         ...metrics,
//         { field: `train_${metric.name}` },
//         { field: `test_${metric.name}` },
//         { field: `val_${metric.name}` },
//       ];
//     }

//     // extract parameters
//     let distinctParameters = {};
//     for (const run of rawRuns) {
//       distinctParameters = { ...distinctParameters, ...run.parameters };
//     }
//     const parameters = Object.keys(distinctParameters).map((name) => {
//       return { field: name };
//     });

//     // column grouping
//     const columnGroupingModel = [
//       { groupId: "Actions", children: [...actionsColumns] },
//       { groupId: "Info", children: [...initialColumns] },
//       { groupId: "Metrics", children: [...metrics] },
//       { groupId: "Parameters", children: [...parameters] },
//     ];

//     // column visibility
//     let columnVisibilityModel = {
//       last_modified: false,
//       start_time: false,
//       end_time: false,
//     };
//     [...metrics, ...parameters].forEach((col) => {
//       if (col.field.includes("test")) {
//         return; // skip this iteration and proceed with the next one
//       }
//       columnVisibilityModel = { ...columnVisibilityModel, [col.field]: false };
//     });

//     const columns = [
//       ...actionsColumns,
//       ...initialColumns,
//       ...metrics,
//       ...parameters,
//     ];

//     return { columns, columnGroupingModel, columnVisibilityModel };
//   };

//   const getRuns = async () => {
//     setLoading(true);
//     try {
//       const runs = await getRunsRequest(experimentId);
//       const experiment = await getExperimentById(experimentId);
//       const metrics = await getComponentsRequest({
//         selectTypes: ["Metric"],
//         relatedComponent: experiment.task_name,
//       });
//       const rows = extractRows(runs);
//       const rowsWithStringStatus = rows.map((run) => {
//         return { ...run, status: getRunStatus(run.status) };
//       });
//       const { columns, columnGroupingModel, columnVisibilityModel } =
//         extractColumns(metrics, runs);
//       setRows(rowsWithStringStatus);
//       setColumns(columns);
//       setColumnGroupingModel(columnGroupingModel);
//       setColumnVisibilityModel(columnVisibilityModel);
//     } catch (error) {
//       enqueueSnackbar("Error while trying to obtain the runs table.");
//       if (error.response) {
//         console.error("Response error:", error.message);
//       } else if (error.request) {
//         console.error("Request error", error.request);
//       } else {
//         console.error("Unknown Error", error.message);
//       }
//     } finally {
//       setLoading(false);
//     }
//   };

//   // fetch the runs and preprocess the data for DataGrid
//   useEffect(() => {
//     if (experimentId !== undefined) {
//       getRuns();
//     }
//   }, [experimentId]);
//   return (
//     <Paper
//       sx={{
//         p: 4,
//       }}
//     >
//       {experimentId === undefined && (
//         <Alert severity="warning" sx={{ mb: 2 }}>
//           <AlertTitle>No experiment selected</AlertTitle>
//           Select an experiment to see the runs associated to it
//         </Alert>
//       )}
//       {!loading ? (
//         <DataGrid
//           rows={
//             experimentId
//               ? rows.filter((run) => String(run.experiment_id) === experimentId)
//               : []
//           }
//           columns={columns}
//           initialState={{
//             pagination: {
//               paginationModel: {
//                 pageSize: 10,
//               },
//             },
//             columns: {
//               columnVisibilityModel,
//             },
//           }}
//           experimentalFeatures={{ columnGrouping: true }}
//           columnGroupingModel={columnGroupingModel}
//           slots={{
//             toolbar: GridToolbar,
//           }}
//           pageSizeOptions={[10]}
//           density="compact"
//           disableRowSelectionOnClick
//           autoHeight
//           sx={{
//             // disable cell selection style
//             ".MuiDataGrid-cell:focus": {
//               outline: "none",
//             },
//             // pointer cursor on ALL rows
//             "& .MuiDataGrid-row:hover": {},
//           }}
//         />
//       ) : (
//         <CircularProgress color="inherit" />
//       )}
//     </Paper>
//   );
// }

// RunsTable.propTypes = {
//   experimentId: PropTypes.string,
// };

// RunsTable.defaultProps = {
//   experimentId: undefined,
// };

// export default RunsTable;

/// EXPERIMENTAL ///

//Falta considerar:
//--Identificar el tipo de Task del experimento, solamente esta para Tabular ahora
//--Pantalla en Nulo si no está habilitada para esa Task
//--Permitir visualizar solo a contenido Finished
//--Buscar los datos reales
//--

import React, { useState } from "react";
import { Button, Dialog, DialogActions, DialogContent, DialogTitle, Box } from "@mui/material";
import Plot from "react-plotly.js";

function RunsTable() {
  const [openPopup, setOpenPopup] = useState(false);
  const [selectedChart, setSelectedChart] = useState("radar");
  const [selectedParameters, setSelectedParameters] = useState(["Parametro 1", "Parametro 2", "Parametro 3", "Parametro 4"]);

  const handleOpenPopup = () => {
    setOpenPopup(true);
  };

  const handleClosePopup = () => {
    setOpenPopup(false);
  };

  const handleChangeChart = (chartType) => {
    setSelectedChart(chartType);
  };

  const handleToggleParameter = (parameter) => {
    const updatedParameters = selectedParameters.includes(parameter)
      ? selectedParameters.filter((param) => param !== parameter)
      : [...selectedParameters, parameter];

    setSelectedParameters(updatedParameters);
  };

  // Datos del gráfico (reemplaza esto con tus datos reales)
  const datosModelo1 = {
    type: "scatterpolar",
    r: [4, 3, 2, 5], // Datos del Modelo 1 para los parámetros 1, 2, 3, 4
    theta: selectedParameters,
    fill: "toself",
    name: "Modelo 1",
  };

  const datosModelo2 = {
    type: "scatterpolar",
    r: [3, 4, 3, 4], // Datos del Modelo 2 para los parámetros 1, 2, 3, 4
    theta: selectedParameters,
    fill: "toself",
    name: "Modelo 2",
  };

  const barData = [
    {
      x: selectedParameters,
      y: [4, 3, 2, 5], // Datos del Modelo 1 para los parámetros 1, 2, 3, 4
      type: 'bar',
      name: 'Modelo 1'
    },
    {
      x: selectedParameters,
      y: [3, 4, 3, 4], // Datos del Modelo 2 para los parámetros 1, 2, 3, 4
      type: 'bar',
      name: 'Modelo 2'
    }
  ];

  const pieDataModelo1 = [
    {
      labels: selectedParameters,
      values: [4, 3, 2, 5], // Datos del Modelo 1
      type: 'pie',
      name: 'Modelo 1'
    }
  ];

  const pieDataModelo2 = [
    {
      labels: selectedParameters,
      values: [3, 4, 3, 4], // Datos del Modelo 2
      type: 'pie',
      name: 'Modelo 2'
    }
  ];

  return (
    <>
      {/* Botón para abrir el popup */}
      <Button variant="contained" color="primary" onClick={handleOpenPopup}>
        Open Popup
      </Button>

      {/* Diálogo (Popup) */}
      <Dialog open={openPopup} onClose={handleClosePopup} maxWidth="md" fullWidth>
        <DialogTitle>Comparación de Modelos</DialogTitle>
        <DialogContent style={{ display: "flex", flexDirection: "column", alignItems: "center" }}>
          {/* Botones de selección de gráfico */}
          <Box p={2} mb={2} display="flex" justifyContent="center">
            <Button
              variant="text"
              color={selectedChart === "radar" ? "primary" : "inherit"}
              onClick={() => handleChangeChart("radar")}
              style={{ borderBottom: selectedChart === "radar" ? "2px solid #00bebb" : "2px solid #ffffff", marginRight: "30px" }}
            >
              Radar
            </Button>
            <Button
              variant="text"
              color={selectedChart === "bar" ? "primary" : "inherit"}
              onClick={() => handleChangeChart("bar")}
              style={{ borderBottom: selectedChart === "bar" ? "2px solid #00bebb" : "2px solid #ffffff", marginRight: "30px" }}
            >
              Bar
            </Button>
            <Button
              variant="text"
              color={selectedChart === "pie" ? "primary" : "inherit"}
              onClick={() => handleChangeChart("pie")}
              style={{ borderBottom: selectedChart === "pie" ? "2px solid #00bebb" : "2px solid #ffffff", marginRight: "30px" }}
            >
              Pie
            </Button>
          </Box>

          {/* Contenedor de parámetros y gráfico */}
          <Box display="flex" flexDirection="row" alignItems="flex-start">
            {/* Contenedor de parámetros */}
            <Box bgcolor="#2F2F2F" p={2} mr={2} display="flex" flexDirection="column" alignItems="center">
              {["Parametro 1", "Parametro 2", "Parametro 3", "Parametro 4"].map((param) => (
                <Button
                  key={param}
                  variant={selectedParameters.includes(param) ? "contained" : "outlined"}
                  color="primary"
                  onClick={() => handleToggleParameter(param)}
                  style={{ marginBottom: "10px" }}
                >
                  {param}
                </Button>
              ))}
            </Box>

            {/* Gráfico Plotly */}
            <Plot
              data={
                selectedChart === "radar"
                  ? [datosModelo1, datosModelo2]
                  : selectedChart === "bar"
                  ? barData
                  : selectedChart === "pie"
                  ? [...pieDataModelo1, ...pieDataModelo2]
                  : []
              }
              layout={{
                polar: { radialaxis: { visible: selectedChart === "radar", range: [0, 5] } },
                showlegend: true,
                width: 600,
                height: 400,
              }}
            />
          </Box>


          {/* Otro contenido del popup (si es necesario) */}
          <p>Otro contenido del popup...</p>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleClosePopup} color="primary">
            Close
          </Button>
        </DialogActions>
      </Dialog>
    </>
  );
}

export default RunsTable;