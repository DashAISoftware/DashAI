import React, { useState, useEffect } from "react";

import { CircularProgress, Grid, TextField, Typography } from "@mui/material";
import PropTypes from "prop-types";
import { useSnackbar } from "notistack";

import { getComponents as getComponentsRequest } from "../../api/component";
import ItemSelectorWithInfo from "../custom/ItemSelectorWithInfo";

function SetNameAndExplainerStep({ newExpl, setNewExpl, setNextEnabled }) {
  const { enqueueSnackbar } = useSnackbar();
  const [loading, setLoading] = useState(false);

  // explainer name state
  const [nModifications, setNModifications] = useState(0);
  const [explNameOk, setExplNameOk] = useState(false);
  const [explNameError, setExplNameError] = useState(false);

  const [explainers, setExplainers] = useState([]);
  const [selectedExplainer, setSelectedExplainer] = useState({});

  const getExplainers = async () => {
    setLoading(true);
    try {
      const explainers = await getComponentsRequest({
        selectTypes: ["Explainer"],
      });
      setExplainers(explainers);
      if (typeof newExpl.name === "string" && newExpl.name !== "") {
        const previouslySelectedExplainer =
          explainers.find((explainer) => explainer.name === newExpl.name) || {};
        setSelectedExplainer(previouslySelectedExplainer);
      }
    } catch (error) {
      enqueueSnackbar("Error while trying to obtain the explainers list.");
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

  const handleNameInputChange = (event) => {
    setNewExpl({ ...newExpl, name: event.target.value });
    setNModifications(nModifications + 1);

    if (nModifications + 1 >= 4) {
      if (event.target.value.length < 4) {
        setExplNameError(true);
        setExplNameOk(false);
      } else {
        setExplNameError(false);
        setExplNameOk(true);
      }
    }
  };

  useEffect(() => {
    getExplainers();
  }, []);

  useEffect(() => {
    if (explNameOk) {
      setNextEnabled(true);
    } else {
      setNextEnabled(false);
    }
  }, [explNameOk]);

  return (
    <Grid
      container
      direction="row"
      justifyContent="space-around"
      alignItems="stretch"
      spacing={2}
    >
      {/* Set Name subcomponent */}
      <Grid item xs={12}>
        <Typography variant="subtitle1" component="h3" sx={{ mb: 3 }}>
          Enter a name and select the task for the new experiment
        </Typography>

        <TextField
          id="experiment-name-input"
          label="Explainer name"
          value={newExpl.name}
          fullWidth
          onChange={handleNameInputChange}
          autoComplete="off"
          sx={{ mb: 2 }}
          error={explNameError}
          helperText="The experiment name must have at least 4 alphanumeric characters."
        />
      </Grid>

      {/* Tasks Subcomponent */}
      <Grid item xs={12}>
        <Grid container spacing={1}>
          {/* Tasks list and description */}
          {!loading ? (
            <ItemSelectorWithInfo
              itemsList={explainers}
              selectedItem={selectedExplainer}
              setSelectedItem={setSelectedExplainer}
            />
          ) : (
            <CircularProgress color="inherit" />
          )}
        </Grid>
      </Grid>
    </Grid>
  );
}

SetNameAndExplainerStep.propTypes = {
  newExpl: PropTypes.shape({
    id: PropTypes.string,
    name: PropTypes.string,
  }),
  setNewExpl: PropTypes.func.isRequired,
  setNextEnabled: PropTypes.func.isRequired,
};

export default SetNameAndExplainerStep;
