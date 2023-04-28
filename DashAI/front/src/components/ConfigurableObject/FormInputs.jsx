import React, { useState, useEffect } from "react";
import {
  TextField,
  MenuItem,
  Stack,
  Typography,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  FormControlLabel,
  Checkbox,
  FormControl,
} from "@mui/material";
import SettingsIcon from "@mui/icons-material/Settings";
import { generateTooltip } from "../ParameterForm";
import PropTypes from "prop-types";
import { getDefaultValues } from "../../utils/values";
import Subform from "./Subform";
import { styled } from "@mui/material/styles";

const Input = styled(TextField)(({ theme }) => ({
  minWidth: "20vw",
}));

export function Integer({ name, value, onChange, description, error }) {
  return (
    <div key={name}>
      <Input
        variant="outlined"
        label={name}
        name={name}
        value={value}
        onChange={onChange}
        error={error}
        helperText={error}
        type="number"
        margin="dense"
      />
      {generateTooltip(description)}
    </div>
  );
}
Integer.propTypes = {
  name: PropTypes.string.isRequired,
  value: PropTypes.number.isRequired,
  onChange: PropTypes.func.isRequired,
  description: PropTypes.string.isRequired,
  error: PropTypes.string,
};
Integer.defaultProps = {
  error: undefined,
};

// This field is designed to handle non-integer numeric inputs
export function Number({ name, value, onChange, description, error }) {
  return (
    <div key={name}>
      <Input
        variant="outlined"
        label={name}
        name={name}
        value={value}
        onChange={onChange}
        error={error}
        helperText={error}
        margin="dense"
      />
      {generateTooltip(description)}
    </div>
  );
}
Number.propTypes = {
  name: PropTypes.string.isRequired,
  value: PropTypes.number.isRequired,
  onChange: PropTypes.func.isRequired,
  description: PropTypes.string.isRequired,
  error: PropTypes.string,
};
Number.defaultProps = {
  error: undefined,
};

export function Float({ name, value, onChange, description, error }) {
  return (
    <div key={name}>
      <Input
        variant="outlined"
        label={name}
        name={name}
        value={value}
        type="number"
        onChange={onChange}
        error={error}
        helperText={error}
        margin="dense"
      />
      {generateTooltip(description)}
    </div>
  );
}
Float.propTypes = {
  name: PropTypes.string.isRequired,
  value: PropTypes.number.isRequired,
  onChange: PropTypes.func.isRequired,
  description: PropTypes.string.isRequired,
  error: PropTypes.string,
};
Float.defaultProps = {
  error: undefined,
};

export function Text({ name, value, onChange, error, description }) {
  return (
    <div key={name}>
      <Input
        name={name}
        label={name}
        defaultValue={value}
        onKeyUp={onChange}
        error={error}
        helperText={error}
        margin="dense"
      />
      {generateTooltip(description)}
    </div>
  );
}
Text.propTypes = {
  name: PropTypes.string.isRequired,
  value: PropTypes.string,
  onChange: PropTypes.func.isRequired,
  description: PropTypes.string.isRequired,
  error: PropTypes.string,
};
Text.defaultProps = {
  value: "",
  error: undefined,
};

export function Select({ name, value, onChange, error, description, options }) {
  return (
    <div key={name}>
      <Input
        select
        name={name}
        label={name}
        value={value}
        onChange={onChange}
        error={error}
        helperText={error}
        margin="dense"
      >
        {options.map((option) => (
          <MenuItem key={option} value={option}>
            {option}
          </MenuItem>
        ))}
      </Input>
      {generateTooltip(description)}
    </div>
  );
}
Select.propTypes = {
  name: PropTypes.string.isRequired,
  value: PropTypes.string.isRequired,
  onChange: PropTypes.func.isRequired,
  description: PropTypes.string.isRequired,
  error: PropTypes.string,
  options: PropTypes.arrayOf(PropTypes.string).isRequired,
};
Select.defaultProps = {
  error: undefined,
};

export function Boolean({ name, value, onChange, error, description }) {
  return (
    <div key={name}>
      <FormControl error={error}>
        <FormControlLabel
          label={name}
          control={<Checkbox name={name} checked={value} onChange={onChange} />}
        />
      </FormControl>
      {generateTooltip(description)}
    </div>
  );
}
Boolean.propTypes = {
  name: PropTypes.string.isRequired,
  value: PropTypes.bool.isRequired,
  onChange: PropTypes.func.isRequired,
  description: PropTypes.string.isRequired,
  error: PropTypes.string,
};
Boolean.defaultProps = {
  error: undefined,
};

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
      {generateTooltip(paramJsonSchema.description)}
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

export function genInput(objName, paramJsonSchema, formik, defaultValues) {
  const { type, properties } = paramJsonSchema;
  // Props that are common to almost all form inputs.
  const commonProps = {
    name: objName,
    value: formik.values[objName],
    onChange: formik.handleChange,
    error: formik.errors[objName],
    description: paramJsonSchema.description,
    key: objName,
  };
  switch (type) {
    case "object":
      return (
        <Stack key={objName} spacing={3}>
          {Object.keys(properties).map((parameter) =>
            genInput(
              parameter,
              properties[parameter].oneOf[0],
              formik,
              defaultValues[parameter]
            )
          )}
        </Stack>
      );
    case "class":
      return (
        <ClassInput
          name={objName}
          paramJsonSchema={paramJsonSchema}
          setFieldValue={formik.setFieldValue}
          formDefaultValues={defaultValues}
          key={`rec-param-${objName}`}
        />
      );
    case "integer":
      return <Integer {...commonProps} />;
    case "number":
      return <Number {...commonProps} />;
    case "string":
      return <Select {...commonProps} options={paramJsonSchema.enum} />;
    case "text":
      return <Text {...commonProps} />;
    case "boolean":
      return <Boolean {...commonProps} />;
    case "float":
      return <Float {...commonProps} />;
    default:
      return (
        <Typography variant="p" sx={{ color: "red" }}>
          {`Not a valid parameter type ${type}`}
        </Typography>
      );
  }
}
