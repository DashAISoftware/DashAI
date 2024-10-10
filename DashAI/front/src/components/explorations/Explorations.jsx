import React, { useState } from "react";
import uuid from "react-uuid";

import { Button, Stack, Box, Typography } from "@mui/material";
import {
  AddCircleOutline as AddIcon,
  Update as UpdateIcon,
} from "@mui/icons-material";

import { useSnackbar } from "notistack";
import {
  useExplorationsContext,
  explorationModes,
  contextDefaults,
} from "./context";
import { ExplorationsTable, ExplorationEditor } from "./";
import { getExplorersByExplorationId } from "../../api/explorer";

function Explorations() {
  const {
    explorationMode,
    setExplorationMode,
    explorationData,
    setExplorationData,
  } = useExplorationsContext();
  const { dataset_id } = explorationData;
  const { enqueueSnackbar } = useSnackbar();

  const [updateFlag, setUpdateFlag] = useState(false);

  const handleCreateExploration = () => {
    setExplorationData((prev) => ({ ...prev, id: uuid() }));
    setExplorationMode(explorationModes.EXPLORATION_CREATE);
  };

  const handleCloseDialogs = () => {
    setExplorationData((prev) => ({
      ...contextDefaults.defaultExplorationData,
      dataset_id: prev.dataset_id,
    }));
    setExplorationMode(contextDefaults.defaultExplorationMode);
    handleReload();
  };

  const handleReload = () => {
    setUpdateFlag(true);
  };

  const fetchExplorers = async (explorationId) => {
    return await getExplorersByExplorationId(explorationId)
      .then((data) => {
        return data;
      })
      .catch((error) => {
        enqueueSnackbar("Error while trying to fetch explorers", {
          variant: "error",
        });
        return [];
      });
  };

  const handleSelectExploration = (data) => {
    fetchExplorers(data.id).then((explorers) => {
      setExplorationData((prev) => ({ ...prev, ...data, explorers }));
      setExplorationMode(explorationModes.EXPLORATION_EDIT);
    });
  };

  const handleRunExploration = (data) => {
    fetchExplorers(data.id).then((explorers) => {
      setExplorationData((prev) => ({ ...prev, ...data, explorers }));
      setExplorationMode(explorationModes.EXPLORATION_RUN);
    });
  };

  return (
    <React.Fragment>
      <Stack direction="row" alignItems="center" spacing={2} pl={2} pr={2}>
        {/* Show titles if they exist */}
        {explorationMode.title && (
          <Box sx={{ flexGrow: 1, textAlign: "start" }}>
            <Typography variant="h6" component="div">
              {explorationMode.title}
            </Typography>

            {explorationMode.body && (
              <Typography variant="body1" component="div">
                {explorationMode.body}
              </Typography>
            )}
          </Box>
        )}

        {/* Show creator */}
        {explorationMode.creatorButton && (
          <Button
            variant="contained"
            onClick={handleCreateExploration}
            startIcon={<AddIcon />}
          >
            Create
          </Button>
        )}

        {/* Show reloader */}
        {explorationMode.reloaderButton && (
          <Button
            variant="contained"
            onClick={handleReload}
            endIcon={<UpdateIcon />}
          >
            Update
          </Button>
        )}
      </Stack>

      <Box
        sx={{
          overflowY: "auto",
          overflowX: "auto",
          mt: 2,
          mb: 2,
          height: "calc(100vh - 300px)",
          display: "flex",
          flexDirection: "column",
          justifyContent: "center",
          alignItems: "center",
          gap: 1,
        }}
      >
        <ExplorationsTable
          updateTableFlag={updateFlag}
          setUpdateTableFlag={setUpdateFlag}
          datasetId={dataset_id}
          onExplorationSelect={handleSelectExploration}
          onExplorationRun={handleRunExploration}
        />

        {explorationMode === explorationModes.EXPLORATION_CREATE && (
          <ExplorationEditor
            open={true}
            handleCloseDialog={handleCloseDialogs}
          />
        )}

        {explorationMode === explorationModes.EXPLORATION_EDIT && (
          <ExplorationEditor
            open={true}
            handleCloseDialog={handleCloseDialogs}
          />
        )}
      </Box>
    </React.Fragment>
  );
}

export default Explorations;
