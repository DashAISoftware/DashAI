import React, { useState, useEffect } from "react";
import { GridActionsCellItem } from "@mui/x-data-grid";
import { parseRangeToIndex } from "../../utils/parseRange";
import PropTypes from "prop-types";
import {
  Box,
  IconButton,
  Typography,
  Button,
  ButtonGroup,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  TextField,
  RadioGroup,
  FormControlLabel,
  Radio,
  Stack,
  DialogContentText,
} from "@mui/material";
import { styled } from "@mui/material/styles";
import { TrackChanges, ArrowBackOutlined } from "@mui/icons-material";
import BoxWithTitle from "../shared/BoxWithTitle";
import InputWithDebounce from "../shared/InputWithDebounce";
import { parseIndexToRange } from "../../utils/parseRange";

const ConverterScopeModal = ({
  converterToConfigure,
  updateScope,
  scopeInitialValues,
  datasetInfo,
}) => {
  const [open, setOpen] = useState(false);
  const [inputError, setInputError] = useState({
    columns: "",
    rows: "",
  });
  const [selectedRadioButtons, setSelectedRadioButtons] = useState({
    columns: "all-columns",
    rows: "all-rows",
  });
  const [scope, setScope] = useState({
    columns: "",
    rows: "",
  });

  const totalColumns = datasetInfo.total_columns;
  const totalRows = datasetInfo.total_rows;

  const handleRadioChange = (event) => {
    const radioToUpdate = event.target.name;
    const value = event.target.value;
    setSelectedRadioButtons((previousState) => ({
      ...previousState,
      [radioToUpdate]: value,
    }));
    // Clean the error message so the user can save the changes when uses all columns or rows
    setInputError((previousError) => ({
      ...previousError,
      [radioToUpdate]: "",
    }));
    // Clean the input field when the user selects a radio button
    // It helps to avoid inconsistencies between the input field and the error now not displayed
    setScope((previousState) => ({
      ...previousState,
      [radioToUpdate]: "",
    }));
  };

  const handleInputChange = (scopeToUpdate, value) => {
    // If the user writes a custom range, we update the radio button
    setSelectedRadioButtons((previousState) => ({
      ...previousState,
      [scopeToUpdate]: "custom-" + scopeToUpdate,
    }));

    try {
      const maxValue = scopeToUpdate === "columns" ? totalColumns : totalRows;
      // Check if the range is valid
      parseRangeToIndex(value, maxValue);
      setInputError((previousError) => ({
        ...previousError,
        [scopeToUpdate]: "",
      }));
      // Update the scope with the new range
      // Local state uses string values
      setScope((previousState) => ({
        ...previousState,
        [scopeToUpdate]: value,
      }));
    } catch (error) {
      setInputError((previousError) => ({
        ...previousError,
        [scopeToUpdate]: error.message,
      }));
    }
  };

  const handleOnSave = () => {
    let errors = false;
    if (
      selectedRadioButtons.columns === "custom-columns" &&
      scope.columns === ""
    ) {
      setInputError((previousError) => ({
        ...previousError,
        columns: "Please specify the columns range",
      }));
      errors = true;
    }
    if (selectedRadioButtons.rows === "custom-rows" && scope.rows === "") {
      setInputError((previousError) => ({
        ...previousError,
        rows: "Please specify the rows range",
      }));
      errors = true;
    }
    if (errors) {
      return;
    }
    // By this point, we know that the scope can be parsed
    const columnsArray =
      selectedRadioButtons.columns === "all-columns"
        ? []
        : parseRangeToIndex(scope.columns, totalColumns);
    const rowsArray =
      selectedRadioButtons.rows === "all-rows"
        ? []
        : parseRangeToIndex(scope.rows, totalRows);
    const newScope = {
      columns: columnsArray,
      rows: rowsArray,
    };
    // Parent component uses arrays
    updateScope(newScope);
    setOpen(false);
  };

  const handleOnCancel = () => {
    setOpen(false);
  };

  // When the modal is opened, we reset the state to the initial values
  // This is useful when the user opens the modal multiple times after clicking on the save or back buttons
  useEffect(() => {
    setInputError({
      columns: "",
      rows: "",
    });
    setSelectedRadioButtons({
      columns:
        scopeInitialValues.columns.length === 0
          ? "all-columns"
          : "custom-columns",
      rows: scopeInitialValues.rows.length === 0 ? "all-rows" : "custom-rows",
    });
    setScope({
      columns:
        scopeInitialValues.columns.length === 0
          ? ""
          : parseIndexToRange(scopeInitialValues.columns).join(","),
      rows:
        scopeInitialValues.rows.length === 0
          ? ""
          : parseIndexToRange(scopeInitialValues.rows).join(","),
    });
  }, [open]);

  return (
    <React.Fragment>
      <GridActionsCellItem
        key="edit-scope-button"
        icon={<TrackChanges />}
        label="Set scope"
        onClick={() => setOpen(true)}
      >
        Set scope
      </GridActionsCellItem>
      <Dialog open={open} onClose={() => setOpen(false)}>
        <DialogTitle>
          <Box display="flex" alignItems="center">
            <IconButton onClick={() => setOpen(false)}>
              <ArrowBackOutlined />
            </IconButton>
            <Typography variant="h5" sx={{ ml: 2 }}>
              {converterToConfigure} scope
            </Typography>
          </Box>
        </DialogTitle>
        <DialogContent>
          <Stack spacing={4} sx={{ py: 2 }} transition="ease">
            <DialogContentText>
              The selected range will be used to train the converter and should
              be type-compatible with its input.
            </DialogContentText>
            <BoxWithTitle title="Columns">
              <Box
                sx={{
                  px: 2,
                  overflowY: "auto",
                  py: 4,
                  height: "auto",
                  width: "inherit",
                  transition: "opacity 0.3s ease",
                }}
              >
                <RadioGroup
                  name="columns"
                  value={selectedRadioButtons.columns}
                  onChange={handleRadioChange}
                >
                  <FormControlLabel
                    value="all-columns"
                    control={<Radio />}
                    label="Use all columns of the dataset"
                    sx={{ my: 1 }}
                  />
                  <FormControlLabel
                    value="custom-columns"
                    control={<Radio />}
                    label="Specify the range from which this converter will learn"
                    sx={{ my: 1 }}
                  />
                  <React.Fragment>
                    <InputWithDebounce
                      variant="outlined"
                      id="custom-columns"
                      label={"Column(s)"}
                      name={"columns"}
                      value={scope.columns}
                      onChange={(value) => handleInputChange("columns", value)}
                      error={inputError["columns"] !== ""}
                      helperText={inputError["columns"]}
                    />
                  </React.Fragment>
                </RadioGroup>
              </Box>
            </BoxWithTitle>
          </Stack>
          <Stack spacing={4} sx={{ py: 2 }} transition="ease">
            <BoxWithTitle title="Rows">
              <Box
                sx={{
                  px: 2,
                  overflowY: "auto",
                  py: 4,
                  height: "auto",
                  width: "inherit",
                  transition: "opacity 0.3s ease",
                }}
              >
                <RadioGroup
                  name="rows"
                  value={selectedRadioButtons.rows}
                  onChange={handleRadioChange}
                >
                  <FormControlLabel
                    value="all-rows"
                    control={<Radio />}
                    label="Use all rows of the dataset"
                    sx={{ my: 1 }}
                  />
                  <FormControlLabel
                    value="custom-rows"
                    control={<Radio />}
                    label="Specify the range from which this converter will learn"
                    sx={{ my: 1 }}
                  />
                  <React.Fragment>
                    <InputWithDebounce
                      variant="outlined"
                      id="custom-rows"
                      label={"Row(s)"}
                      name={"rows"}
                      value={scope.rows}
                      onChange={(value) => handleInputChange("rows", value)}
                      error={inputError["rows"] !== ""}
                      helperText={inputError["rows"]}
                    />
                  </React.Fragment>
                </RadioGroup>
              </Box>
            </BoxWithTitle>
          </Stack>
        </DialogContent>
        <DialogActions>
          <ButtonGroup>
            <Button onClick={handleOnCancel}>Back</Button>
            <Button
              variant="contained"
              onClick={handleOnSave}
              disabled={inputError.columns !== "" || inputError.rows !== ""}
            >
              Save
            </Button>
          </ButtonGroup>
        </DialogActions>
      </Dialog>
    </React.Fragment>
  );
};

export default ConverterScopeModal;

ConverterScopeModal.propTypes = {
  converterToConfigure: PropTypes.string,
  updateScope: PropTypes.func.isRequired,
  datasetInfo: PropTypes.shape({
    total_columns: PropTypes.number,
    total_rows: PropTypes.number,
  }),
};

ConverterScopeModal.defaultProps = {
  converterToConfigure: "",
  datasetInfo: {
    total_columns: 0,
    total_rows: 0,
  },
};

const Input = styled(TextField)(({ theme }) => ({
  width: "20vw",
}));
