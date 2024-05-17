// columns that are common to all runs
import React from "react";
import { styled } from "@mui/material";
import { formatDate } from "../../../utils";

// style for the cells in the initial columns
const StyledCell = styled("div")(({ theme, color }) => ({
  display: "inline-block",
  padding: theme.spacing(0.5),
  borderRadius: theme.shape.borderRadius,
  backgroundColor: color,
}));

export const initialColumns = [
  {
    field: "name",
    headerName: "Name",
    minWidth: 150,
  },
  {
    field: "model_name",
    headerName: "Model",
    minWidth: 250,
    renderCell: (params) => {
      let color;
      switch (params.value) {
        case "RandomForestClassifier":
          color = "#FF8A65";
          break;
        case "LogisticRegression":
          color = "#64B5F6";
          break;
        case "KNeighborsClassifier":
          color = "#FFD54F";
          break;
        case "HistGradientBoostingClassifier":
          color = "#9575CD";
          break;
        case "DummyClassifier":
          color = "#4DB6AC";
          break;
        case "SVC":
          color = "#FF80AB";
          break;
        default:
          color = "#795548";
          break;
      }
      return <StyledCell color={color}>{params.value}</StyledCell>;
    },
  },
  {
    field: "status",
    headerName: "Status",
    minWidth: 160,
    renderCell: (params) => {
      let color;
      switch (params.value) {
        case "Not Started":
          color = "#626262";
          break;
        case "Finished":
          color = "#43A047";
          break;
        case "Running":
          color = "#FFEA00";
          break;
        case "Error":
          color = "#A70909";
          break;
        default:
          break;
      }
      return <StyledCell color={color}>{params.value}</StyledCell>;
    },
  },
  {
    field: "created",
    headerName: "Created",
    type: Date,
    minWidth: 140,
    valueFormatter: (params) => formatDate(params.value),
  },
  {
    field: "last_modified",
    headerName: "Last modified",
    type: Date,
    minWidth: 140,
    valueFormatter: (params) => formatDate(params.value),
  },
  {
    field: "start_time",
    headerName: "Start",
    type: Date,
    minWidth: 140,
    valueFormatter: (params) => formatDate(params.value),
  },
  {
    field: "end_time",
    headerName: "End",
    type: Date,
    minWidth: 140,
    valueFormatter: (params) => formatDate(params.value),
  },
];
