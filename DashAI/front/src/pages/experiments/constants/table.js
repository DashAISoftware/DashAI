import { formatDate } from "../../../utils";

export const experimentsColumns = [
  {
    field: "id",
    headerName: "ID",
    minWidth: 30,
    editable: false,
  },
  {
    field: "name",
    headerName: "Name",
    minWidth: 250,
    editable: false,
  },
  {
    field: "task_name",
    headerName: "Task",
    minWidth: 200,
    editable: false,
  },
  {
    field: "dataset_id",
    headerName: "Dataset",
    minWidth: 200,
    editable: false,
  },
  {
    field: "created",
    headerName: "Created",
    minWidth: 140,
    editable: false,
    valueFormatter: (params) => formatDate(params.value),
  },
  {
    field: "last_modified",
    headerName: "Edited",
    type: Date,
    minWidth: 140,
    editable: false,
    valueFormatter: (params) => formatDate(params.value),
  },
];

export const datasetsColumns = [
  {
    field: "name",
    headerName: "Name",
    minWidth: 250,
    editable: false,
  },
  {
    field: "created",
    headerName: "Created",
    minWidth: 200,
    type: Date,
    valueFormatter: (params) => formatDate(params.value),

    editable: false,
  },
  {
    field: "last_modified",
    headerName: "Last modified",
    minWidth: 200,
    type: Date,
    valueFormatter: (params) => formatDate(params.value),
    editable: false,
  },
];

export const runnersColumns = [
  {
    field: "name",
    headerName: "Name",
    minWidth: 250,
    editable: false,
  },
  {
    field: "model_name",
    headerName: "Model Name",
    minWidth: 300,
    editable: false,
  },
  {
    field: "status",
    headerName: "Status",
    minWidth: 150,
    editable: false,
  },
];
