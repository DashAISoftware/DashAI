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
  Collapse,
  Paper,
} from "@mui/material";
import SettingsIcon from "@mui/icons-material/Settings";
import Subform from "../Subform";
import { getDefaultValues } from "../../../utils/values";
import {
  getChildren as getChildrenRequest,
  getModelSchema as getModelSchemaRequest,
  getSchema as getSchemaRequest,
} from "../../../api/oldEndpoints";
/**
 * This component handles the case when a field in a form is itself another form (recursive parameter).
 * It allows the user to choose configurable objects of a specific class (indicated in the parent form's JSON)
 * and renders a subform with the object that the user chooses.
 * @param {string} name name of the recursive parameter to use as an identifier
 * @param {object} paramJsonSchema JSON object of the default recursive parameter
 * @param {function} setFieldValue formik function to change the value of a parameter by its name
 * @param {object}  formDefaultValues default values for the default recursive parameter
 *
 */
function ClassInput({
  name,
  paramJsonSchema,
  setFieldValue,
  formDefaultValues,
}) {
  const modal = false;
  const [options, setOptions] = useState([]);
  const [selectedOption, setSelectedOption] = useState(
    formDefaultValues.choice,
  );
  const [open, setOpen] = useState(false);
  const [paramSchema, setParamSchema] = useState({});
  const [defaultValues, setDefaultValues] = useState(formDefaultValues);
  const [loading, setLoading] = useState(true);

  const getOptions = async (parentClass) => {
    try {
      const options = await getChildrenRequest(parentClass);
      setOptions(options);
    } catch (error) {
      if (error.response) {
        console.error("Response error:", error.message);
      } else if (error.request) {
        console.error("Request error", error.request);
      } else {
        console.error("Unkown Error", error.message);
      }
    } finally {
      //
    }
  };

  const getParamSchema = async () => {
    if (selectedOption !== "") {
      setLoading(true);
      try {
        let schema;
        if (selectedOption === "splits") {
          schema = await getSchemaRequest("dataloader", selectedOption);
        } else {
          schema = await getModelSchemaRequest(selectedOption);
        }
        setParamSchema(schema);
        setDefaultValues(
          formDefaultValues.choice !== selectedOption
            ? getDefaultValues(schema)
            : formDefaultValues,
        );
      } catch (error) {
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
    }
  };

  const handleClose = () => {
    setOpen(false);
  };

  const handleButtonClick = () => {
    if (modal) {
      setOpen(true);
    } else {
      setOpen(!open);
    }
  };

  // fetch the configurable objects that have a specific parent
  useEffect(() => {
    getOptions(paramJsonSchema.parent);
  }, []);

  // fetch the json schema of a specific configurable object based on the choice the user makes
  useEffect(() => {
    getParamSchema();
  }, [selectedOption]);

  return (
    <div key={name}>
      {/* Dropdown to select a configurable object to render a subform */}
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

      {/* Button to show the modal that contains the subform */}
      <IconButton color="primary" component="label" onClick={handleButtonClick}>
        <SettingsIcon />
      </IconButton>

      {/* Option 1: Collapsible component that contains the subform */}
      <Collapse in={open} sx={{ mt: 1, display: modal ? "none" : "show" }}>
        <Paper variant="outlined" sx={{ p: 2 }}>
          {!loading && (
            <Subform
              name={name}
              parameterSchema={paramSchema}
              setFieldValue={setFieldValue}
              choice={selectedOption}
              defaultValues={defaultValues}
            />
          )}
        </Paper>
      </Collapse>
      {/* Option 2: Modal that contains the subform */}
      <Dialog
        open={open}
        onClose={handleClose}
        sx={{ display: modal ? "show" : "none" }}
      >
        <DialogTitle>{`${selectedOption} parameters`}</DialogTitle>
        <DialogContent key={selectedOption}>
          {!loading && (
            <Subform
              name={name}
              parameterSchema={paramSchema}
              setFieldValue={setFieldValue}
              choice={selectedOption}
              defaultValues={defaultValues}
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
    PropTypes.oneOfType([PropTypes.string, PropTypes.bool, PropTypes.object]),
  ).isRequired,
  setFieldValue: PropTypes.func.isRequired,
  formDefaultValues: PropTypes.objectOf(
    PropTypes.oneOfType([
      PropTypes.string,
      PropTypes.bool,
      PropTypes.number,
      PropTypes.object,
    ]),
  ),
};

ClassInput.defaultProps = {
  formDefaultValues: { emptyDefaultValues: true },
};

export default ClassInput;
