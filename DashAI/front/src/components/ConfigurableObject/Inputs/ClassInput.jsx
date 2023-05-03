import React, { useState, useEffect } from "react";
import PropTypes from "prop-types";
import FormTooltip from "../FormTooltip";
import { Input } from "../../../styles/components/InputStyles";
import {
  IconButton,
  MenuItem,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
} from "@mui/material";
import SettingsIcon from "@mui/icons-material/Settings";
import Subform from "../Subform";
import { getDefaultValues } from "../../../utils/values";

function ClassInput({
  name,
  paramJsonSchema,
  setFieldValue,
  formDefaultValues,
}) {
  const [options, setOptions] = useState([]);
  const [selectedOption, setSelectedOption] = useState(
    formDefaultValues.choice
  );
  const [open, setOpen] = useState(false);
  const [paramSchema, setParamSchema] = useState({});
  const [defaultValues, setDefaultValues] = useState({
    loaded: true,
    values: formDefaultValues,
  });
  const handleButtonClick = () => {
    setOpen(true);
  };
  const getOptions = async (parentClass) => {
    const fetchedOptions = await fetch(
      `${process.env.REACT_APP_GET_CHILDREN_ENDPOINT + parentClass}`
    );
    const receivedOptions = await fetchedOptions.json();
    setOptions(receivedOptions);
  };
  const getParamSchema = async () => {
    if (selectedOption !== "") {
      setDefaultValues({ ...defaultValues, loaded: false });
      let fetchedParams;
      if (selectedOption === "splits") {
        fetchedParams = await fetch(
          `http://localhost:8000/api/v0/select/dataloader/${selectedOption}`
        );
      } else {
        fetchedParams = await fetch(
          `${process.env.REACT_APP_SELECT_MODEL_ENDPOINT + selectedOption}`
        );
      }
      const parameterSchema = await fetchedParams.json();
      setParamSchema(parameterSchema);
      setDefaultValues({
        loaded: true,
        values:
          formDefaultValues.choice !== selectedOption
            ? getDefaultValues(parameterSchema)
            : formDefaultValues,
      });
    }
  };
  const handleClose = () => {
    setOpen(false);
  };
  useEffect(() => {
    getOptions(paramJsonSchema.parent);
  }, []);
  useEffect(() => {
    getParamSchema();
  }, [selectedOption]);
  return (
    <div key={name}>
      <Input
        select
        label={name}
        name="choice"
        value={selectedOption}
        onChange={(e) => setSelectedOption(e.target.value)}
      >
        {options.map((option) => (
          <MenuItem key={option} value={option}>
            {option}
          </MenuItem>
        ))}
      </Input>
      <FormTooltip contentStr={paramJsonSchema.description} />
      <IconButton color="primary" component="label" onClick={handleButtonClick}>
        <SettingsIcon />
      </IconButton>
      <Dialog open={open} onClose={handleClose}>
        <DialogTitle>{`${selectedOption} parameters`}</DialogTitle>
        <DialogContent key={selectedOption}>
          {defaultValues.loaded && (
            <Subform
              name={name}
              parameterSchema={paramSchema}
              setFieldValue={setFieldValue}
              choice={selectedOption}
              defaultValues={defaultValues.values}
            />
          )}
        </DialogContent>
        <DialogActions>
          <Button variant="outlined" onClick={handleClose} autoFocus>
            Save
          </Button>
        </DialogActions>
      </Dialog>
    </div>
  );
}

ClassInput.propTypes = {
  name: PropTypes.string.isRequired,
  paramJsonSchema: PropTypes.objectOf(
    PropTypes.oneOfType([PropTypes.string, PropTypes.bool, PropTypes.object])
  ).isRequired,
  setFieldValue: PropTypes.func.isRequired,
  formDefaultValues: PropTypes.objectOf(
    PropTypes.oneOfType([
      PropTypes.string,
      PropTypes.bool,
      PropTypes.number,
      PropTypes.object,
    ])
  ),
};

ClassInput.defaultProps = {
  formDefaultValues: { emptyDefaultValues: true },
};

export default ClassInput;
