import React, { useState, useEffect } from "react";

import { CircularProgress, Grid, TextField, Typography } from "@mui/material";
import PropTypes from "prop-types";
import { useSnackbar } from "notistack";

import { getComponents as getComponentsRequest } from "../../api/component";
import ItemSelectorWithInfo from "../custom/ItemSelectorWithInfo";

function SetNameAndExplainerStep({
  newExpl,
  setNewExpl,
  setNextEnabled,
  scope,
}) {
  const { enqueueSnackbar } = useSnackbar();
  const [loading, setLoading] = useState(false);

  // explainer name state
  const [nModifications, setNModifications] = useState(0);
  const [explNameOk, setExplNameOk] = useState(false);
  const [explNameError, setExplNameError] = useState(false);

  const [explainers, setExplainers] = useState([]);
  const [selectedExplainer, setSelectedExplainer] = useState({});
  const [selectedExplainerOk, setSelectedExplainerOk] = useState(false);

  const getExplainers = async () => {
    setLoading(true);
    try {
      const explainers = await getComponentsRequest({
        selectTypes: [`${scope}Explainer`],
      });
      setExplainers(explainers);
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
    if (selectedExplainer && "name" in selectedExplainer) {
      setNewExpl({
        ...newExpl,
        explainer_name: selectedExplainer.name,
      });
      setSelectedExplainerOk(true);
    }
  }, [selectedExplainer]);

  useEffect(() => {
    getExplainers();
  }, []);

  useEffect(() => {
    if (typeof newExpl.name === "string" && newExpl.name.length >= 4) {
      setExplNameOk(true);
      setNModifications(4);
    }
  }, []);

  useEffect(() => {
    if (explNameOk && selectedExplainerOk) {
      setNextEnabled(true);
    } else {
      setNextEnabled(false);
    }
  }, [explNameOk, selectedExplainerOk]);

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
          Select a global explainer and enter a name
        </Typography>

        <TextField
          id="explainer-name-input"
          label="Explainer name"
          value={newExpl.name}
          fullWidth
          onChange={handleNameInputChange}
          autoComplete="off"
          sx={{ mb: 2 }}
          error={explNameError}
          helperText="The explainer name must have at least 4 alphanumeric characters."
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
    name: PropTypes.string,
    explainer_name: PropTypes.string,
    dataset_id: PropTypes.number,
    parameters: PropTypes.object,
    fit_parameters: PropTypes.object,
  }),
  setNewExpl: PropTypes.func.isRequired,
  setNextEnabled: PropTypes.func.isRequired,
  scope: PropTypes.string.isRequired,
};

export default SetNameAndExplainerStep;
