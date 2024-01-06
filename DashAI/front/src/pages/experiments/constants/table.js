import { formatDate } from "../../../utils";

export const initialColumns = [
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
