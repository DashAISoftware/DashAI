import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Drawer, Typography, Divider } from "@mui/material";
import { getExperiments as getExperimentsRequest } from "../api/experiment";
import { useSnackbar } from "notistack";
import ItemSelector from "./custom/ItemSelector";

const drawerWidth = "15vw";
/**
 * Permanent drawer that allows the user to select an experiment to see its associated runs
 */
function ExperimentsDrawer() {
  const { enqueueSnackbar } = useSnackbar();
  const navigate = useNavigate();

  const [experiments, setExperiments] = useState([]);
  const [selectedExperiment, setSelectedExperiment] = useState({});
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (selectedExperiment && "id" in selectedExperiment) {
      navigate(`/app/results/experiments/${selectedExperiment.id}`);
    }
  }, [selectedExperiment]);

  const getExperiments = async () => {
    setLoading(true);
    try {
      const experiments = await getExperimentsRequest();
      setExperiments(experiments);
    } catch (error) {
      enqueueSnackbar("Error while trying to obtain the experiment table.", {
        variant: "error",
        anchorOrigin: {
          vertical: "top",
          horizontal: "right",
        },
      });
      if (error.response) {
        console.error("Response error:", error.message);
      } else if (error.request) {
        console.error("Request error", error.request);
      } else {
        console.error("Unkown Error", error.message);
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    getExperiments();
  }, []);

  return (
    <Drawer
      sx={{
        width: drawerWidth,
        flexShrink: 0,
        "& .MuiDrawer-paper": {
          width: drawerWidth,
          boxSizing: "border-box",
          backgroundColor: "#212121",
          zIndex: 1099,
          overflowX: "auto",
        },
      }}
      variant="persistent"
      anchor="left"
      open={true}
    >
      {/* Title */}
      <Typography
        variant="h6"
        component="div"
        sx={{ py: 2, mt: 10, alignSelf: "center" }}
      >
        Experiments
      </Typography>
      <Divider />

      {/* Selector of experiments */}
      {!loading && (
        <ItemSelector
          itemsList={experiments}
          selectedItem={selectedExperiment}
          setSelectedItem={setSelectedExperiment}
        />
      )}
    </Drawer>
  );
}

export default ExperimentsDrawer;
