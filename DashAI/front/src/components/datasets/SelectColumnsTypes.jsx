import React, { useEffect, useState } from "react";
import { Paper, Grid, Typography, TextField } from "@mui/material";
import SelectInput from "../ConfigurableObject/Inputs/SelectInput";
import PropTypes from "prop-types";
import { parseRangeToIndex } from "../../utils/parseRange";

function SelectColumnsTypes({ newDataset }) {
  const totalColumns = 100;
  const [textFields, setTextFields] = useState([
    { id: 1, columns: [], type: "" },
  ]);
  const [columnsRangeError, setColumnsRangeError] = useState(false);
  const [columnsRangeErrorText, setColumnsRangeErrorText] = useState("");

  const typesList = [
    "null",
    "bool",
    "int8",
    "int16",
    "int32",
    "int64",
    "uint8",
    "uint16",
    "uint32",
    "uint64",
    "float16",
    "float32 (alias float)",
    "float64 (alias double)",
    "time32[(s|ms)]",
    "time64[(us|ns)]",
    "timestamp[(s|ms|us|ns)]",
    "timestamp[(s|ms|us|ns), tz=(tzstring)]",
    "date32",
    "date64",
    "duration[(s|ms|us|ns)]",
    "decimal128(precision, scale)",
    "decimal256(precision, scale)",
    "binary",
    "large_binary",
    "string",
    "large_string",
  ];

  const handleColumnsChange = (id, value) => {
    try {
      const columnsIndex = parseRangeToIndex(value, totalColumns);
      const updatedTextFields = textFields.map((textField) =>
        textField.id === id
          ? { ...textField, columns: columnsIndex }
          : textField,
      );
      setTextFields(updatedTextFields);
      setColumnsRangeError(false);
      // Add a new TextField when the last TextField is focused
      if (id === textFields.length && value !== "") {
        setTextFields([
          ...updatedTextFields,
          { id: id + 1, columns: [], type: "" },
        ]);
      }
    } catch (error) {
      setColumnsRangeErrorText(error.message);
      setColumnsRangeError(true);
    }
  };

  const handleTypeChange = (id, value) => {
    const updatedTextFields = textFields.map((textField) =>
      textField.id === id ? { ...textField, type: value } : textField,
    );
    setTextFields(updatedTextFields);
  };

  useEffect(() => {
    console.log(textFields);
  }, [textFields]);

  return (
    <Paper
      variant="outlined"
      sx={{ p: 4, maxHeight: "55vh", overflow: "auto" }}
    >
      <Grid container direction={"column"} alignItems={"center"}>
        <Grid item>
          <Typography variant="subtitle1">
            Choose and cast type columns
          </Typography>
        </Grid>
        <Grid item>
          <Typography
            item
            variant="caption"
            component="h3"
            sx={{ mb: 2, color: "grey" }}
          >
            Introduce the index of the columns that you want to cast. The
            notation is based on ranges. For example: 1-6, 23-108
          </Typography>
        </Grid>
      </Grid>
      <Grid item>
        {textFields.map((textField) => (
          <Grid container spacing={2} key={textField.id}>
            <Grid xs={8}>
              <TextField
                label="Columns"
                id="dataset-cast-columns"
                onChange={(e) =>
                  handleColumnsChange(textField.id, e.target.value)
                }
                error={columnsRangeError}
                helperText={columnsRangeErrorText}
                size="small"
              />
            </Grid>
            <Grid xs={4}>
              <SelectInput
                name={"Type"}
                size="small"
                value={textField.type}
                setFieldValue={(name, value) =>
                  handleTypeChange(textField.id, value)
                }
                description={"Choose the type of the columns"}
                options={typesList}
                optionNames={typesList}
              />
            </Grid>
          </Grid>
        ))}
      </Grid>
    </Paper>
  );
}
SelectColumnsTypes.propTypes = {
  newDataset: PropTypes.bool.isRequired,
};
export default SelectColumnsTypes;
