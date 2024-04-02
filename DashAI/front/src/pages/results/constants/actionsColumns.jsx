// columns related to open details of runs
import React from "react";
import QueryStatsIcon from "@mui/icons-material/QueryStats";
import { GridActionsCellItem } from "@mui/x-data-grid";

export const actionsColumns = (handleRunResultsOpen) => [
    {
      field: "actions",
      headerName: "Details",
      type: "actions",
      minWidth: 80,
      getActions: (params) => [
        <GridActionsCellItem
          key="specific-results-button"
          icon={<QueryStatsIcon />}
          label="Run Results"
          onClick={() => {handleRunResultsOpen( params.id )}}
          sx={{ color: "primary.main" }}
        />,
      ],
    },
  ];