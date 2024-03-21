/* eslint-disable react/prop-types */
import { Box, Chip } from "@mui/material";
import Menu from "@mui/material/Menu";
import MenuItem from "@mui/material/MenuItem";
import React, { useState } from "react";
import ModelSchemaFields from "./ModelSchemaFields";

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
function ModalSchemaFieldsWithOptions({ title, options, field, ...rest }) {
  const [selectedType, setSelectedType] = useState(getType(field.value));
  const [anchorEl, setAnchorEl] = useState(null);

  const handleTypeChange = (type) => {
    field.onChange(
      type === "null"
        ? null
        : options.find((option) => option.type === type).placeholder,
    );
    setSelectedType(type);
    setAnchorEl(null);
  };

  const handleMenuOpen = (event) => {
    setAnchorEl(event.currentTarget);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  const fieldProps = {
    paramJsonSchema: {
      title,
      ...options.find((option) => option.type === selectedType),
    },
    field,
    ...rest,
  };

  return (
    <>
      <Box display="flex" gap={2}>
        <Box flex={1}>
          <ModelSchemaFields {...fieldProps} />
        </Box>
        <Box pt={2.5}>
          <Chip
            label={typesLabels[selectedType]}
            sx={{ width: 72, borderRadius: 2 }}
            variant="outlined"
            onClick={handleMenuOpen}
          />
        </Box>
      </Box>

      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleMenuClose}
      >
        {options?.map(({ type }) => (
          <MenuItem key={type} onClick={() => handleTypeChange(type)}>
            {typesLabels[type]}
          </MenuItem>
        ))}
      </Menu>
    </>
  );
}

export default ModalSchemaFieldsWithOptions;
