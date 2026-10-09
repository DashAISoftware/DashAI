import React, { useEffect, useState, useMemo } from "react";
import FormSchemaField from "./FormSchemaField";
import SingleSelectChipGroup from "./SingleSelectChipGroup";
import { getValidator } from "../../utils/schema";
import PropTypes from "prop-types";
import FormSchemaFieldCard from "./FormSchemaFieldCard";

/**
 * Renders an anyOf field as a card.
 * The type-selector chip group (String / Int / Float / Null) lives in the card header.
 * The body renders the appropriate input for the selected type.
 */
const typesLabels = {
  string: "String",
  integer: "Int",
  number: "Float",
  null: "Null",
};

const getType = (value, options) => {
  if (value === null || value === undefined) {
    return "null";
  }
  if (typeof value === "number") {
    if (
      Number.isInteger(value) &&
      options.some((opt) => opt.type === "integer")
    ) {
      return "integer";
    }
    return "number";
  }
  return "string";
};

function FormSchemaFieldWithOptions({
  title,
  description,
  required,
  options,
  field,
  objName,
  placeholder,
  setError,
  disabled = false,
  ...rest
}) {
  const [selectedType, setSelectedType] = useState(null);
  const [errorField, setErrorField] = useState(null);

  const paramJsonSchema = useMemo(
    () => ({
      title,
      description,
      required,
      ...options.find((option) => option.type === selectedType),
    }),
    [title, description, required, options, selectedType],
  );

  const fieldProps = { paramJsonSchema, field, objName, disabled, ...rest };

  const handleSetError = (error) => {
    setErrorField(error);
    setError && setError(Boolean(error));
  };

  const handleTypeChange = (type) => {
    if (type === "null") {
      handleSetError(null);
    }
    field.onChange(type === "null" ? null : placeholder);
    setSelectedType(type);
  };

  useEffect(() => {
    if (field.value !== undefined && selectedType === null) {
      setSelectedType(getType(field.value, options));
    }

    if (selectedType && selectedType !== "null" && fieldProps.paramJsonSchema) {
      const validator = getValidator(fieldProps.paramJsonSchema);
      validator
        .strict()
        .validate(field.value)
        .then(() => handleSetError(null))
        .catch((err) => handleSetError(err.message));
    }
  }, [selectedType, field.value, fieldProps.paramJsonSchema]);

  const chipGroup = selectedType ? (
    <SingleSelectChipGroup
      options={options.map(({ type }) => ({
        key: type,
        label: typesLabels[type],
      }))}
      onChange={handleTypeChange}
      selected={selectedType}
      disabled={disabled}
    />
  ) : null;

  return (
    <FormSchemaFieldCard
      label={title}
      paramKey={objName}
      description={description}
      headerRight={chipGroup}
    >
      <FormSchemaField {...fieldProps} error={errorField} />
    </FormSchemaFieldCard>
  );
}

FormSchemaFieldWithOptions.propTypes = {
  title: PropTypes.string.isRequired,
  description: PropTypes.string,
  required: PropTypes.bool,
  options: PropTypes.array.isRequired,
  field: PropTypes.object.isRequired,
  objName: PropTypes.string,
  placeholder: PropTypes.any,
  setError: PropTypes.func,
  disabled: PropTypes.bool,
};

export default FormSchemaFieldWithOptions;
