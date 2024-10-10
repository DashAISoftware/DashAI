import React, { useCallback, useEffect, useState } from "react";
import PropTypes, { exact } from "prop-types";
import uuid from "react-uuid";

import {
  Button,
  Grid,
  Box,
  TextField,
  Typography,
  Tooltip,
  Autocomplete,
  autocompleteClasses,
  CircularProgress,
} from "@mui/material";
import { AddCircleOutline as AddIcon } from "@mui/icons-material";

import { useSnackbar } from "notistack";

import useSchema from "../../../hooks/useSchema";
import { useExplorationsContext, contextDefaults } from "../context";
import { ExplorersTable } from "../";

import { getComponents } from "../../../api/component";

const renderOption = (props, option, _, ownerState) => {
  const { key, ...optionProps } = props;
  return (
    <Tooltip
      title={
        <Typography
          component="span"
          variant="inherit"
          sx={{ whiteSpace: "pre-line" }}
        >
          {option.reason}
        </Typography>
      }
      placement="right"
      key={key}
    >
      <span>
        <Box
          sx={{
            [`&.${autocompleteClasses.option}`]: {},
          }}
          component="li"
          {...optionProps}
        >
          {ownerState.getOptionLabel(option)}
        </Box>
      </span>
    </Tooltip>
  );
};

function ConfigureExplorersStep({ onValidation = () => {} }) {
  const {
    explorationData,
    setExplorationData,
    explorerData,
    setExplorerData,
    datasetColumns,
  } = useExplorationsContext();

  const { enqueueSnackbar } = useSnackbar();

  const [loading, setLoading] = useState(true);
  const [options, setOptions] = useState([]);
  const [value, setValue] = useState(null);
  const [inputValue, setInputValue] = useState("");

  const validateOptions = useCallback((data) => {
    const options = data.map((explorer, index) => {
      const allowedDtypes = explorer.metadata.allowed_dtypes;
      const restrictedDtypes = explorer.metadata.restricted_dtypes;
      const inputCardinality = explorer.metadata.input_cardinality;
      let disabled = false;
      let reason = "";

      let validColumns = datasetColumns;
      // check the valid dataset columns for the explorer
      if (!allowedDtypes.includes("*")) {
        validColumns = datasetColumns.filter((col) =>
          allowedDtypes.includes(col.dataType),
        );
      }

      // check the restricted dataset columns for the explorer
      if (
        restrictedDtypes.some((dtype) =>
          datasetColumns.some((col) => col.dataType === dtype),
        )
      ) {
        validColumns = validColumns.filter(
          (col) => !restrictedDtypes.includes(col.dataType),
        );
      }

      // check the input cardinality
      if (
        inputCardinality.exact != undefined &&
        inputCardinality.exact != null
      ) {
        if (validColumns.length < inputCardinality.exact) disabled = true;

        reason += `This explorer requires exactly \
        ${inputCardinality.exact} valid ${
          inputCardinality.exact === 1 ? "column" : "columns"
        }.`;
      } else {
        if (inputCardinality.min != undefined && inputCardinality.min != null) {
          if (validColumns.length < inputCardinality.min) disabled = true;

          reason += `This explorer requires at least \
            ${inputCardinality.min} valid ${
            inputCardinality.min === 1 ? "column" : "columns"
          }.`;
        }

        if (inputCardinality.max != undefined && inputCardinality.max != null) {
          if (reason) reason += "\n";
          reason += `This explorer requires at most \
            ${inputCardinality.max} valid ${
            inputCardinality.max === 1 ? "column" : "columns"
          }.`;
        }
      }

      if (validColumns.length > 0) {
        reason += `\n\n\
          The dataset has the following valid columns: \n\
          ${validColumns
            .map((col) => ` - ${col.columnName}: ${col.dataType}`)
            .join("\n")}`;
      }

      if (!allowedDtypes.includes("*")) {
        reason += `\n\n\
          This explorer only accepts columns with data types: \n\
          ${allowedDtypes.map((dtype) => ` - ${dtype}`).join("\n")}`;
      }

      if (restrictedDtypes.length > 0) {
        reason += `\n\n\
          This explorer does NOT accept columns with data types: \n\
          ${restrictedDtypes.map((dtype) => ` - ${dtype}`).join("\n")}`;
      }

      return {
        id: index,
        label: explorer.name,
        value: explorer,
        validColumns,
        disabled,
        reason,
      };
    });

    return options;
  }, []);

  const getAvailableExplorers = () => {
    setLoading(true);
    getComponents({
      selectTypes: ["Explorer"],
    })
      .then((data) => {
        const validatedOptions = validateOptions(data);
        setOptions(validatedOptions);
      })
      .catch((error) => {
        enqueueSnackbar("Error while trying to fetch explorers", {
          variant: "error",
        });
      })
      .finally(() => {
        setLoading(false);
      });
  };

  const handleSelectExplorer = (_, newValue) => {
    setValue(newValue);
    if (!newValue) {
      setExplorerData((prev) => ({
        ...prev,
        exploration_type: "",
        columns: [],
      }));
      return;
    }

    let explorationType = newValue.value.name;
    let columns = newValue.validColumns;
    const maxColumns = newValue.value.metadata.input_cardinality.max;
    if (maxColumns && columns.length > maxColumns) {
      // take only the first maxColumns columns
      columns = columns.slice(0, maxColumns);
    }

    const exactColumns = newValue.value.metadata.input_cardinality.exact;
    if (exactColumns && columns.length !== exactColumns) {
      // take only the first exactColumns columns
      columns = columns.slice(0, exactColumns);
    }

    setExplorerData((prev) => ({
      ...prev,
      columns,
      exploration_type: explorationType,
    }));
  };

  const { defaultValues: defaultParameters } = useSchema({
    modelName: explorerData.exploration_type,
  });
  const handleAddButton = () => {
    const newExplorer = { ...explorerData };
    newExplorer.parameters = defaultParameters;
    newExplorer.id = uuid();

    setExplorationData((prev) => ({
      ...prev,
      explorers: [...prev.explorers, newExplorer],
    }));

    const validColumnsCount = value.validColumns.length;
    const columns = newExplorer.columns.length;
    if (columns < validColumnsCount) {
      enqueueSnackbar(
        `Some columns were ignored to match the explorer's input cardinality`,
        {
          variant: "info",
        },
      );
    }

    setExplorerData((prev) => ({
      ...prev,
      name: "",
      exploration_type: "",
      columns: [],
      parameters: {},
    }));
    setValue(null);
  };

  // checks if there is at least 1 model added to enable the "Next" button
  useEffect(() => {
    if (explorationData.explorers.length > 0) {
      onValidation(true);
    } else {
      onValidation(false);
    }
  }, [explorationData.explorers]);

  // in mount, fetches the compatible explorers with the dataset
  useEffect(() => {
    getAvailableExplorers();
  }, []);

  return (
    <Grid
      container
      direction="row"
      justifyContent="space-around"
      alignItems="stretch"
      spacing={2}
    >
      <Grid item xs={12}>
        <Typography variant="subtitle1" component="h3">
          Add explorers to your exploration
        </Typography>
      </Grid>

      {/* Form to add a single explorer to the exploration */}
      <Grid item xs={12}>
        <Grid container direction="row" columnSpacing={3} wrap="nowrap">
          <Grid item xs={4} md={12}>
            <TextField
              label="Name (optional)"
              value={explorerData.name}
              onChange={(e) =>
                setExplorerData({ ...explorerData, name: e.target.value })
              }
              fullWidth
            />
          </Grid>

          <Grid item xs={4} md={12}>
            <Autocomplete
              loading={loading}
              disablePortal
              options={options}
              getOptionDisabled={(option) => option.disabled}
              isOptionEqualToValue={(option, value) => option.id === value.id}
              fullWidth
              renderInput={(params) => (
                <TextField {...params} label="Select a explorer to add" />
              )}
              renderOption={renderOption}
              inputValue={inputValue}
              onInputChange={(_, newInputValue) => {
                setInputValue(newInputValue);
              }}
              value={value}
              onChange={handleSelectExplorer}
            />
          </Grid>

          <Grid item xs={1} md={2}>
            <Button
              variant="outlined"
              disabled={!value || value.disabled}
              startIcon={<AddIcon />}
              onClick={handleAddButton}
              sx={{ height: "100%" }}
            >
              Add
            </Button>
          </Grid>
        </Grid>
      </Grid>

      {/* Explorers table */}
      <Grid item xs={12}>
        {loading && (
          <Box
            sx={{
              display: "flex",
              justifyContent: "center",
              alignItems: "center",
              height: "40vh",
            }}
          >
            <CircularProgress />
          </Box>
        )}

        {!loading && <ExplorersTable explorerTypes={options} />}
      </Grid>
    </Grid>
  );
}

ConfigureExplorersStep.propTypes = {};

export default ConfigureExplorersStep;
