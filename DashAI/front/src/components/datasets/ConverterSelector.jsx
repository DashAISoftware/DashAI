import React, { useEffect, useState, useCallback } from "react";
import {
  Grid,
  TextField,
  MenuItem,
  InputAdornment,
  IconButton,
  Tooltip,
} from "@mui/material";
import ConverterEditorModal from "./ConverterEditorModal";
import { useSnackbar } from "notistack";
import { Help } from "@mui/icons-material";

import { getComponents as getComponentsRequest } from "../../api/component";
import uuid from "react-uuid";
import PropTypes from "prop-types";

const ConverterSelector = ({ updateAppliedConvertersList }) => {
  const { enqueueSnackbar } = useSnackbar();
  const [loading, setLoading] = useState(true);
  const [converters, setConverters] = useState([]);

  const [newConverter, setNewConverter] = useState({
    name: "",
    schema: {},
  });

  const getCompatibleConverters = useCallback(async () => {
    setLoading(true);
    try {
      const converters = await getComponentsRequest({
        selectTypes: ["Converter"],
      });
      setConverters(converters);
    } catch (error) {
      enqueueSnackbar("Error while trying to obtain compatible converters");
      if (error.response) {
        console.error("Response error:", error.message);
      } else if (error.request) {
        console.error("Request error", error.request);
      } else {
        console.error("Unknown Error", error.message);
      }
    } finally {
      setLoading(false);
    }
  }, []);

  // Fetch converters on mount
  useEffect(() => {
    getCompatibleConverters();
  }, []);

  const handleAddConverter = (parameters) => {
    updateAppliedConvertersList((prev) => [
      ...prev,
      {
        id: uuid(),
        order: prev.length + 1,
        name: newConverter.name,
        schema: newConverter.schema,
        parameters: { ...parameters },
      },
    ]);
  };

  return (
    <Grid container>
      <Grid container direction="row" columnSpacing={3} wrap="nowrap" mb={1}>
        {/* New converter to apply */}
        <Grid item xs={8} md={12}>
          <TextField
            select
            fullWidth
            label="Select converter"
            value={newConverter.name}
            onChange={(event) => {
              let converter = converters.find(
                (c) => c.name === event.target.value,
              );
              setNewConverter(converter);
            }}
            disabled={loading}
            InputProps={{
              endAdornment: newConverter.description ? (
                <InputAdornment
                  position="end"
                  sx={{
                    marginRight: 4,
                  }}
                >
                  <Tooltip title={newConverter.description} placement="top">
                    <IconButton>
                      <Help />
                    </IconButton>
                  </Tooltip>
                </InputAdornment>
              ) : null,
            }}
          >
            {converters.map((converter) => (
              <MenuItem key={converter.name} value={converter.name}>
                {converter.name}
              </MenuItem>
            ))}
          </TextField>
        </Grid>

        {/* Open modal to edit new converter */}
        <Grid item xs={4}>
          {/* Converter editor */}
          <ConverterEditorModal
            newConverter={newConverter}
            saveConverter={handleAddConverter}
          />
        </Grid>
      </Grid>
    </Grid>
  );
};

ConverterSelector.propTypes = {
  datasetId: PropTypes.number.isRequired,
  updateAppliedConvertersList: PropTypes.func.isRequired,
};

export default ConverterSelector;
