import React, { useCallback, useEffect, useState } from "react";
import PropTypes from "prop-types";

import {
  Box,
  Autocomplete,
  TextField,
  CircularProgress,
  autocompleteClasses,
  Tooltip,
} from "@mui/material";

import { getComponents } from "../../../api/component";
import { useExplorerContext } from "../context";

const renderOption = (props, option, _, ownerState) => {
  const { key, ...optionProps } = props;
  return option.disabled ? (
    <Tooltip title={option.reason} placement="right" key={key}>
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
  ) : (
    <Box
      key={key}
      sx={{
        [`&.${autocompleteClasses.option}`]: {},
      }}
      component="li"
      {...optionProps}
    >
      {ownerState.getOptionLabel(option)}
    </Box>
  );
};

function StepSelectExplorer({ disableChanges = false }) {
  const {
    explorerData,
    setSelectedExplorer,
    setExplorationName,
    setExplorerConfig,
    setFeedback,
  } = useExplorerContext();
  const { selectedExplorer, selectedColumns, explorationName, explorerConfig } =
    explorerData;
  const columnsCount = selectedColumns.length;
  const columnsDtypes = [
    ...new Set(selectedColumns.map((col) => col.dataType)),
  ];

  const [loading, setLoading] = useState(false);
  const [options, setOptions] = useState([]);
  const [value, setValue] = useState(null);
  const [inputValue, setInputValue] = useState("");
  const [nameChanged, setNameChanged] = useState(
    explorationName !== "" ? true : false,
  );

  const validateOptions = useCallback(
    (data) => {
      const options = data.map((explorer, index) => {
        const allowedDtypes = explorer.metadata.allowed_dtypes;
        const restrictedDtypes = explorer.metadata.restricted_dtypes;
        const inputCardinality = explorer.metadata.input_cardinality;
        let disabled = false;
        let reason = "";

        // check if the explorer is compatible with the selected columns data types
        if (
          !allowedDtypes.includes("*") &&
          !allowedDtypes.some((dtype) => columnsDtypes.includes(dtype))
        ) {
          const nonAllowedTypes = new Set(
            columnsDtypes.filter((dtype) => !allowedDtypes.includes(dtype)),
          );
          disabled = true;
          reason = `Not allowed types: ${Array.from(nonAllowedTypes).join(
            ", ",
          )}`;
        }

        if (restrictedDtypes.some((dtype) => columnsDtypes.includes(dtype))) {
          const restrictedTypes = new Set(
            restrictedDtypes.filter((dtype) => columnsDtypes.includes(dtype)),
          );
          disabled = true;
          reason = `Restricted types: ${Array.from(restrictedTypes).join(
            ", ",
          )}`;
        }

        // check if the explorer is compatible with the selected columns count
        if (
          inputCardinality.min !== undefined &&
          inputCardinality.min !== null &&
          inputCardinality.min > columnsCount
        ) {
          disabled = true;
          reason = `Requires at least ${inputCardinality.min} columns`;
        } else if (
          inputCardinality.max !== undefined &&
          inputCardinality.max !== null &&
          inputCardinality.max < columnsCount
        ) {
          disabled = true;
          reason = `Accepts up to ${inputCardinality.max} columns`;
        } else if (
          inputCardinality.exact !== undefined &&
          inputCardinality.exact !== null &&
          inputCardinality.exact !== columnsCount
        ) {
          disabled = true;
          reason = `Accepts only ${inputCardinality.exact} columns`;
        }

        return {
          label: explorer.name,
          value: explorer,
          disabled,
          reason,
          id: index,
        };
      });
      return options;
    },
    [columnsCount, columnsDtypes],
  );

  const handleSelectExplorer = (_, newValue) => {
    setValue(newValue);
    const newExplorer = newValue?.value?.name || null;
    setSelectedExplorer(newExplorer);

    if (!nameChanged) {
      if (newExplorer) {
        setExplorationName(
          `${newExplorer} ${
            new Date()
              .toISOString() // 2021-10-06T14:00:00.000Z
              .replace(/T/g, "_") // 2021-10-06_14:00:00.000Z
              .replace(/\.\d{3}Z/g, "") // 2021-10-06_14:00:00
              .replace(/:/g, ".") // 2021-10-06_14.00.00
              .replace(/-/g, ".") // 2021.10.06_14.00.00
          }`,
        );
      } else {
        setExplorationName("");
      }
    }

    // set up initial values for explorer config
    const properties = newValue?.value?.schema?.properties || {};
    const placeholders = Object.keys(properties).reduce((acc, key) => {
      const placeholder = properties[key].placeholder || null;
      acc[key] = placeholder;
      return acc;
    }, {});

    // populate explorer config with initial values (do not overwrite existing values)
    setExplorerConfig({
      ...placeholders,
      ...explorerConfig,
    });
  };

  const fetchComponents = async () => {
    setLoading(true);
    getComponents({ selectTypes: ["Explorer"] })
      .then((data) => {
        const validatedOptions = validateOptions(data);
        setOptions(validatedOptions);
        // check if the selected explorer is still valid
        const foundValue =
          validatedOptions.find(
            (option) => option.label === selectedExplorer,
          ) || null;
        if ((foundValue === null || foundValue.disabled) && selectedExplorer) {
          // clear options and display feedback
          setInputValue("");
          setValue(null);
          setSelectedExplorer(null);
          setFeedback({
            show: true,
            type: "warning",
            message: "Explorer no longer valid",
          });
        } else {
          setInputValue(foundValue?.label || "");
          setValue(foundValue || null);
        }
      })
      .catch((err) => {
        console.error(err);
      })
      .finally(() => {
        setLoading(false);
      });
  };

  // fetch components on mount
  useEffect(() => {
    fetchComponents();
  }, []);

  return (
    <Box
      sx={{
        height: "100%",
        width: "100%",
        display: "flex",
        flexDirection: "column",
        justifyContent: "center",
        alignItems: "center",
        gap: 2,
      }}
    >
      {loading && <CircularProgress />}
      {!loading && (
        <React.Fragment>
          <Autocomplete
            loading={loading}
            disablePortal
            options={options}
            getOptionDisabled={(option) => option.disabled}
            isOptionEqualToValue={(option, value) => option.id === value.id}
            sx={{ width: 300 }}
            renderInput={(params) => (
              <TextField {...params} label="ExplorerType*" />
            )}
            readOnly={disableChanges}
            renderOption={renderOption}
            inputValue={inputValue}
            onInputChange={(_, newInputValue) => {
              setInputValue(newInputValue);
            }}
            value={value}
            onChange={handleSelectExplorer}
          />

          <TextField
            label="Exploration Name"
            value={explorationName}
            sx={{ width: 300 }}
            disabled={disableChanges}
            onChange={(e) => {
              let newName = e.target.value;
              newName = newName.trim();
              setExplorationName(e.target.value);
              if (e.target.value !== "") {
                setNameChanged(true);
              } else {
                setNameChanged(false);
              }
            }}
          />
        </React.Fragment>
      )}
    </Box>
  );
}

StepSelectExplorer.propTypes = {};

export default StepSelectExplorer;
