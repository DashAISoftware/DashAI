import React, { useEffect, useMemo, useState } from "react";

import { Box } from "@mui/material";
import { DataGrid } from "@mui/x-data-grid";

import { formatDate } from "../../utils";

import { ExplorerStatus } from "../../types/explorer";
import { getExplorersByDatasetId } from "../../api/explorer";
import { useExplorerContext } from "./context";
import {
  DeleteExplorerAction,
  PinExplorerAction,
  ViewResultAction,
} from "./actions";

function RecentExplorations({
  updateTableFlag = false,
  setUpdateTableFlag = () => {},
}) {
  // Columns definition
  const columns = useMemo(
    () => [
      {
        field: "name",
        headerName: "Recent Explorations",
        flex: 1,
        minwidth: 200,
      },
      {
        field: "status",
        headerName: "Status",
        width: 150,
        valueFormatter: (params) => {
          return ExplorerStatus[params.value];
        },
      },
      {
        field: "updated",
        headerName: "Last Updated",
        width: 200,
        valueGetter: (params) => {
          let date;
          switch (params.row.status) {
            case ExplorerStatus.FINISHED:
              date = params.row.end_time;
              break;
            case ExplorerStatus.STARTED:
              date = params.row.start_time;
              break;
            case ExplorerStatus.DELIVERED:
              date = params.row.delivery_time;
              break;
            default:
              date = params.row.created;
          }
          return formatDate(date);
        },
      },
      {
        field: "actions",
        headerName: "Actions",
        flex: 1,
        minWidth: 150,
        type: "actions",
        getActions: (params) => [
          <ViewResultAction
            key="view"
            explorerId={params.row.id}
            disabled={params.row.id === explorerId}
            status={params.row.status}
          />,
          <PinExplorerAction
            key="pin"
            setUpdateTableFlag={setUpdateTableFlag}
            explorerId={params.row.id}
            disabled={params.row.pinned}
          />,
          <DeleteExplorerAction
            key="delete"
            setUpdateTableFlag={setUpdateTableFlag}
            explorerId={params.row.id}
          />,
        ],
      },
    ],
    [setUpdateTableFlag],
  );

  const { explorerData } = useExplorerContext();
  const { datasetId, explorerId } = explorerData;

  const [loading, setLoading] = useState(false);
  const [explorations, setExplorations] = useState([]);

  const getExplorations = () => {
    setLoading(true);
    getExplorersByDatasetId(datasetId)
      .then((response) => {
        setExplorations(response);
      })
      .catch((error) => {
        console.log(error);
      })
      .finally(() => {
        setLoading(false);
      });
  };

  // Fetch explorations when the component is mounting
  useEffect(() => {
    getExplorations();
  }, []);

  // triggers an update of the table when updateFlag is set to true
  useEffect(() => {
    if (updateTableFlag) {
      setUpdateTableFlag(false);
      getExplorations();
    }
  }, [updateTableFlag]);

  return (
    <Box sx={{ height: "100%", width: "100%" }}>
      <DataGrid
        loading={loading}
        autoHeight
        rows={explorations}
        columns={columns}
        disableRowSelectionOnClick
        initialState={{
          pagination: {
            paginationModel: {
              pageSize: 5,
            },
          },
          sorting: {
            sortModel: [{ field: "updated", sort: "desc" }],
          },
        }}
        pageSizeOptions={[5, 10]}
      />
    </Box>
  );
}

export default RecentExplorations;
