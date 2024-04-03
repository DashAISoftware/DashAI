/* eslint-disable no-unused-vars */
/* eslint-disable react/prop-types */
import { Box, Chip } from "@mui/material";
import Menu from "@mui/material/Menu";
import MenuItem from "@mui/material/MenuItem";
import React, { useState } from "react";
import FormSchemaFields from "./FormSchemaFields";
import SingleSelectChipGroup from "./SingleSelectChipGroup";

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
  options,
  field,
  ...rest
}) {
  const [selectedType, setSelectedType] = useState(getType(field.value));

  const handleTypeChange = (type) => {
    field.onChange(
      type === "null"
        ? null
        : options.find((option) => option.type === type).placeholder,
    );
    setSelectedType(type);
  };

  const fieldProps = {
    paramJsonSchema: {
      title,
      description,
      ...options.find((option) => option.type === selectedType),
    },
    field,
    ...rest,
  };

  return (
    <>
      <Box display="flex" gap={2}>
        <Box flex={1}>
          <FormSchemaFields {...fieldProps} />
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
