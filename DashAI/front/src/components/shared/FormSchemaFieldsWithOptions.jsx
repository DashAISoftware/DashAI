/* eslint-disable no-unused-vars */
/* eslint-disable react/prop-types */
import { Box } from "@mui/material";
import React, { useEffect, useState } from "react";
import FormSchemaFields from "./FormSchemaFields";
import SingleSelectChipGroup from "./SingleSelectChipGroup";
import { getValidator } from "../../utils/schema";

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

// eslint-disable-next-line react/prop-types
function FormSchemaFieldsWithOptions({
  title,
  description,
  required,
  options,
  field,
  ...rest
}) {
  const [selectedType, setSelectedType] = useState(null);
  const [error, setError] = useState(null);

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

  const handleTypeChange = (type) => {
    if (type === "null") {
      setError(null);
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
          setError(null);
        })
        .catch((err) => {
          setError(err.message);
        });
    }
  }, [selectedType, field.value]);

  return (
    <>
      <Box display="flex" gap={2}>
        <Box flex={1}>
          <FormSchemaFields {...fieldProps} error={error} />
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

export default FormSchemaFieldsWithOptions;
