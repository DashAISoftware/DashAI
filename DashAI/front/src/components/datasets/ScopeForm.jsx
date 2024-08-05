import React, { useState } from "react";
import FormInputWrapper from "../configurableObject/Inputs/FormInputWrapper";
import { parseRangeToIndex } from "../../utils/parseRange";
import PropTypes from "prop-types";
import { Grid, TextField } from "@mui/material";
import { styled } from "@mui/material/styles";

const ScopeForm = ({ datasetInfo, setScope, setErrors }) => {
  const [inputError, setInputError] = useState({
    columns: "",
    rows: "",
  });

  const totalColumns = datasetInfo.total_columns;
  const totalRows = datasetInfo.total_rows;

  const handleInputChange = (event) => {
    const keyToUpdate = event.target.name;
    const input = event.target.value.replace(/ /g, ""); // TODO: dont accept spaces between numbers
    const maxValue =
      keyToUpdate === "columns"
        ? totalColumns
        : keyToUpdate === "rows"
        ? totalRows
        : 0;
    try {
      const index = parseRangeToIndex(input, maxValue);
      setInputError((previousError) => ({
        ...previousError,
        [keyToUpdate]: "",
      }));
      setErrors(false);
      setScope((previousColumnOrRow) => ({
        ...previousColumnOrRow,
        [keyToUpdate]: index,
      }));
    } catch (error) {
      setInputError((previousError) => ({
        ...previousError,
        [keyToUpdate]: error.message,
      }));
      setErrors(true);
    }
  };

  return (
    <Grid container direction="column" rowGap={4}>
      <FormInputWrapper
        name="dataset-metadata"
        description={`Specify the value/range to which this converter is to be applied`}
      >
        <Input
          variant="outlined"
          id="dataset-metadata"
          label={"Column(s)"}
          name={"columns"}
          onChange={handleInputChange}
          error={inputError["columns"] !== ""}
          helperText={inputError["columns"]}
        />
      </FormInputWrapper>
      <FormInputWrapper
        name="dataset-metadata"
        description={`Specify the value/range to which this converter is to be applied`}
      >
        <Input
          variant="outlined"
          id="dataset-metadata"
          label={"Row(s)"}
          name={"rows"}
          onChange={handleInputChange}
          error={inputError["rows"] !== ""}
          helperText={inputError["rows"]}
        />
      </FormInputWrapper>
    </Grid>
  );
};

ScopeForm.propTypes = {
  datasetInfo: PropTypes.object.isRequired,
  converterName: PropTypes.string.isRequired,
  scope: PropTypes.object.isRequired,
  setScope: PropTypes.func.isRequired,
  setErrors: PropTypes.func.isRequired,
};

export default ScopeForm;

const Input = styled(TextField)(({ theme }) => ({
  width: "20vw",
}));