import React, { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { Typography, Divider } from "@mui/material";
import { getExperiments as getExperimentsRequest } from "../../api/experiment";
import { useSnackbar } from "notistack";
import ItemSelector from "../custom/ItemSelector";

/**
 * List that allows the user to select an experiment to see its associated runs
 */
function ExperimentsList() {
  const { enqueueSnackbar } = useSnackbar();
  const navigate = useNavigate();
  const { id } = useParams();

  const [experiments, setExperiments] = useState([]);
  const [selectedExperiment, setSelectedExperiment] = useState({});
  const [loading, setLoading] = useState(false);

  // updates url when an experiment from the list is selected
  useEffect(() => {
    if (
      selectedExperiment &&
      "id" in selectedExperiment &&
      parseInt(id) !== selectedExperiment.id // navigates only if a new url is selected
    ) {
      navigate(`/app/results/experiments/${selectedExperiment.id}`);
    }
  }, [selectedExperiment]);

  const getExperiments = async () => {
    setLoading(true);
    try {
      const experiments = await getExperimentsRequest();
      setExperiments(experiments);
      // if there is an id in the url, then initially selects the experiment that corresponds to that id
      if (id !== undefined) {
        setSelectedExperiment(
          experiments.find((exp) => exp.id === parseInt(id)) ?? {},
        );
      }
    } catch (error) {
      enqueueSnackbar("Error while trying to obtain the experiment table.");
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
    getExperiments();
  }, []);

  return (
    <React.Fragment>
      {/* Title */}
      <Typography
        variant="h6"
        component="div"
        sx={{ py: 2, alignSelf: "center" }}
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
    </React.Fragment>
  );
}

export default ExperimentsList;
