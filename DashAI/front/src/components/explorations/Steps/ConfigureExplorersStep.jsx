import React, { useCallback, useEffect, useState } from "react";
import PropTypes from "prop-types";
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
import { useTranslation } from "react-i18next";

import useSchema from "../../../hooks/useSchema";
import { useExplorationsContext } from "../context";
import ExplorersTable from "../ExplorationsTable";

import { getComponents } from "../../../api/component";
import { evaluateColumnEligibility } from "../../../utils/columnEligibility";

/**
 * Render the option for the Autocomplete component with a tooltip.
 * @param {Object} props
 * @param {Object} option - The option object
 * @param {Function} _ - The getOptionLabel function
 * @param {Object} ownerState - The state of the Autocomplete component
 */
const renderOption = (props, option, _, ownerState) => {
  const { key, ...optionProps } = props;
  return (
    <Tooltip
      title={
        <Typography
          component="span"
          variant="body1"
          sx={{ whiteSpace: "pre-line" }}
        >
          {option.tooltip}
        </Typography>
      }
      arrow
      placement="left"
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

/**
 * Exploration step to configure the explorers to use in the exploration
 * @param {Object} props
 * @param {Function} props.onValidation - Callback function to run after the validation of the step
 */
function ConfigureExplorersStep({ onValidation = () => {} }) {
  const {
    explorationData,
    setExplorationData,
    explorerData,
    setExplorerData,
    datasetColumns,
  } = useExplorationsContext();

  const { enqueueSnackbar } = useSnackbar();
  const { t } = useTranslation(["datasets", "common"]);

  const [loading, setLoading] = useState(true);
  const [options, setOptions] = useState([]);
  const [value, setValue] = useState(null);
  const [inputValue, setInputValue] = useState("");

  /**
   * Validates the explorers options based on the dataset columns and the explorer metadata
   * @param {Array} data - The explorer components data
   */
  const validateOptions = useCallback(
    (data) => {
      const options = data.map((explorer, index) => {
        // One shared implementation of the metadata contract, mirroring the
        // backend's validate_columns. This function used to carry its own copy,
        // which read a metadata key the backend had renamed and popped (so it
        // threw on every render) and treated an empty allowed_dtypes list as
        // "nothing allowed" instead of "no restriction" (so every unrestricted
        // explorer ended up disabled).
        const { validColumns, shortfall, restrictions } =
          evaluateColumnEligibility(explorer.metadata, datasetColumns, {
            unknownLabel: t("common:unknown"),
          });

        let tooltip = explorer.description ? `${explorer.description}\n` : "";
        const disabled = shortfall !== null;

        if (validColumns.length === 0) {
          tooltip += `\n${t("datasets:error.noValidColumnsForExplorer")}`;
          if (restrictions.length > 0) {
            tooltip += `\n${t(
              "datasets:error.noValidColumnsWithDtypesMentioned",
              {
                dtypes: restrictions.join(", "),
              },
            )}`;
          }
        } else if (shortfall !== null) {
          const key =
            shortfall.kind === "exact"
              ? "datasets:error.requiresExactColumns"
              : "datasets:error.requiresMinColumns";
          tooltip += `\n${t(key, {
            required: shortfall.required,
            available: shortfall.available,
            count: shortfall.required,
          })}`;
        }

        return {
          id: index,
          label: explorer.metadata.display_name,
          type: explorer.name,
          value: explorer,
          validColumns: validColumns.map((col, order) => ({
            ...col,
            order: order + 1,
          })),
          disabled,
          tooltip,
        };
      });

      return options.sort((a, b) => a.label.localeCompare(b.label));
      // datasetColumns and t were already read inside this callback while the
      // dependency list was empty, so it kept whatever columns were loaded on the
      // first render.
    },
    [datasetColumns, t],
  );

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

  /**
   * Adds the selected explorer to the exploration with the default parameters and
   * appropiate columns.
   */
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

  // checks if there is at least 1 explorer added to enable the "Next" button
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
      spacing={4}
    >
      <Grid size={{ xs: 12 }}>
        <Typography variant="subtitle1" component="h3">
          Add explorers to your exploration
        </Typography>
      </Grid>

      {/* Form to add a single explorer to the exploration */}
      <Grid size={{ xs: 12 }}>
        <Grid container direction="row" columnSpacing={6} wrap="nowrap">
          <Grid size={{ xs: 4, md: 12 }}>
            <TextField
              label="Name (optional)"
              value={explorerData.name}
              onChange={(e) =>
                setExplorerData({ ...explorerData, name: e.target.value })
              }
              fullWidth
            />
          </Grid>

          <Grid size={{ xs: 4, md: 12 }}>
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

          <Grid size={{ xs: 1, md: 2 }}>
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
      <Grid size={{ xs: 12 }}>
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

ConfigureExplorersStep.propTypes = {
  onValidation: PropTypes.func,
};

export default ConfigureExplorersStep;
