import React, { useEffect, useState } from "react";
import PropTypes from "prop-types";
import FormTooltip from "../FormTooltip";
import {
  Box,
  Checkbox,
  FormControl,
  FormControlLabel,
  FormGroup,
  FormLabel,
  Grid,
} from "@mui/material";
/**
 * renders a form field that accepts input for list of strings.
 * @param {string} name name of the input to use as an identifier
 * @param {number} value the value of the input
 * @param {function} onChange function to manage changes in the input
 * @param {string} error text to indicate the reason the validation failed, undefined if there are no errors in validation
 * @param {string} description text to put in a tooltip that helps the user to understand the parameter
 *
 */

const options = ["text", "class"];
function ListOfStringsInput({
  name,
  value,
  onChange,
  description,
  error,
  setFieldValue,
}) {
  const [checkedOptions, setCheckedOptions] = useState({
    text: false,
    class: true,
  });

  const handleChange = (event) => {
    setCheckedOptions({
      ...checkedOptions,
      [event.target.name]: event.target.checked,
    });
  };

  useEffect(() => {
    let checked = [];
    Object.keys(checkedOptions).forEach((option) => {
      if (checkedOptions[option]) {
        checked = [...checked, option];
      }
    });
    setFieldValue(name, checked);
  }, [checkedOptions]);
  return (
    <div key={name}>
      <Grid container direction="row">
        <Grid item>
          <Box sx={{ display: "flex" }}>
            <FormControl sx={{ m: 3 }} component="fieldset" variant="standard">
              <FormLabel component="legend">{name}</FormLabel>
              <FormGroup>
                {options.map((option) => (
                  <FormControlLabel
                    key={option}
                    control={
                      <Checkbox
                        checked={checkedOptions[option]}
                        onChange={handleChange}
                        name={option}
                      />
                    }
                    label={option}
                  />
                ))}
              </FormGroup>
            </FormControl>
          </Box>
        </Grid>
        <Grid item sx={{ mt: 2 }}>
          <FormTooltip contentStr={description} />
        </Grid>
      </Grid>
    </div>
  );
}
ListOfStringsInput.propTypes = {
  name: PropTypes.string.isRequired,
  value: PropTypes.number.isRequired,
  onChange: PropTypes.func.isRequired,
  description: PropTypes.string.isRequired,
  error: PropTypes.string,
  setFieldValue: PropTypes.func.isRequired,
};
ListOfStringsInput.defaultProps = {
  error: undefined,
};

export default ListOfStringsInput;
