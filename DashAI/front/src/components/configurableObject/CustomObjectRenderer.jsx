import { JsonForms, withJsonFormsControlProps } from "@jsonforms/react";
import {
  Button,
  Dialog,
  DialogContent,
  DialogTitle,
  MenuItem,
  TextField,
} from "@mui/material";
import React, { useEffect, useState } from "react";
import { modelA, modelB, modelC } from "../../example_data/JsonFormsSchemas";
import PropTypes from "prop-types";

function CustomObjectRenderer({ renderers, path, handleChange }) {
  const [open, setOpen] = useState(false);
  const [choice, setChoice] = useState("");
  const [selectedSchema, setSelectedSchema] = useState({});
  const [data] = useState({});

  const options = ["ModelA", "ModelB", "ModelC"];
  const components = [modelA, modelB, modelC];

  // when choice changes, selects the appropriate schema to render as a subform
  useEffect(() => {
    const schema = components.find((component) => component.name === choice);
    if (schema !== undefined) {
      setSelectedSchema(schema.schema);
      // setData(initialValues[schema.name]);
    }
  }, [choice]);
  return (
    <React.Fragment>
      {/* Selector of the schema of a recursive parameter */}
      <TextField
        select
        value={choice}
        onChange={(e) => setChoice(e.target.value)}
      >
        {options.map((option) => (
          <MenuItem key={option} value={option}>
            {option}
          </MenuItem>
        ))}
      </TextField>

      {/* Dialog with the form to configure a recursive parameter */}
      <Button onClick={() => setOpen(true)}>Open Modal</Button>
      <Dialog open={open} onClose={() => setOpen(false)}>
        <DialogTitle>Recursive parameter</DialogTitle>
        <DialogContent>
          <JsonForms
            schema={selectedSchema}
            data={data}
            renderers={renderers}
            onChange={({ errors, data }) => {
              handleChange(path, data);
            }}
          />
        </DialogContent>
      </Dialog>
    </React.Fragment>
  );
}

CustomObjectRenderer.propTypes = {
  renderers: PropTypes.arrayOf(
    PropTypes.shape({
      tester: PropTypes.func,
      renderer: PropTypes.func,
    }),
  ).isRequired,
  handleChange: PropTypes.func.isRequired,
  path: PropTypes.string.isRequired,
};

export default withJsonFormsControlProps(CustomObjectRenderer);
