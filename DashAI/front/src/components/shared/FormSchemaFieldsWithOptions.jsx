import { Box } from "@mui/material";
import React, { useEffect, useState } from "react";
import FormSchemaFields from "./FormSchemaFields";
import SingleSelectChipGroup from "./SingleSelectChipGroup";
import { getValidator } from "../../utils/schema";
import PropTypes from "prop-types";

/**
 * This component is a HOC that wraps the FormSchemaFields component and adds a dropdown to select the type of the input
 * @param {string} title title of the input
 * @param {string} description description of the input
 * @param {boolean} required if the input is required
 * @param {array} options array of objects that describe the options for the input
 * @param {object} field object that contains the value of the parameter and a function to set the value
 *
 */
const typesLabels = {
  string: "String",
  integer: "Int",
  null: "Null",
};

const getType = (value) => {
  if (value === null || value === undefined) {
    return "null";
  }
  if (typeof value === "number") {
    return "integer";
  }
  return "string";
};

function FormSchemaFieldsWithOptions({
  title,
  description,
  required,
  options,
  field,
  setError,
  ...rest
}) {
  const [selectedType, setSelectedType] = useState(null);
  const [errorField, setErrorField] = useState(null);

  const fieldProps = {
    paramJsonSchema: {
      title,
      description,
      required,
      ...options.find((option) => option.type === selectedType),
    },
    field,
    ...rest,
  };

  const handleSetError = (error) => {
    setErrorField(error);
    setError && setError(Boolean(error));
  };

  const handleTypeChange = (type) => {
    if (type === "null") {
      handleSetError(null);
    }
    field.onChange(
      type === "null"
        ? null
        : options.find((option) => option.type === type).placeholder,
    );
    setSelectedType(type);
  };

  //  initialize selectedType

  useEffect(() => {
    if (field.value !== undefined && selectedType === null) {
      handleTypeChange(getType(field.value));
    }

    if (selectedType && selectedType !== "null") {
      const validator = getValidator(fieldProps.paramJsonSchema);

      validator
        .strict()
        .validate(field.value)
        .then(() => {
          handleSetError(null);
        })
        .catch((err) => {
          handleSetError(err.message);
        });
    }
  }, [selectedType, field.value]);

  return (
    <>
      <Box display="flex" gap={2}>
        <Box flex={1}>
          <FormSchemaFields {...fieldProps} error={errorField} />
        </Box>
        <Box pt={2.5}>
          <SingleSelectChipGroup
            options={options.map(({ type }) => ({
              key: type,
              label: typesLabels[type],
            }))}
            onChange={(type) => handleTypeChange(type)}
            selected={selectedType}
          />
        </Box>
      </Box>
    </>
  );
}

FormSchemaFieldsWithOptions.propTypes = {
  title: PropTypes.string.isRequired,
  description: PropTypes.string,
  required: PropTypes.bool,
  options: PropTypes.array.isRequired,
  field: PropTypes.object.isRequired,
  setError: PropTypes.func,
};

export default FormSchemaFieldsWithOptions;
