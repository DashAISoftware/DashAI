import React, { useEffect, useState, useCallback } from "react";
import {
  Button,
  Grid,
  TextField,
  MenuItem,
  InputAdornment,
  IconButton,
  Tooltip,
} from "@mui/material";
import { useSnackbar } from "notistack";
import { Help, AddCircleOutline as AddIcon } from "@mui/icons-material";

import { getComponents as getComponentsRequest } from "../../api/component";
import uuid from "react-uuid";
import PropTypes from "prop-types";

const ConverterSelector = ({ setConvertersToApply }) => {
  const { enqueueSnackbar } = useSnackbar();
  const [loading, setLoading] = useState(true);
  const [converters, setConverters] = useState([]);

  const [selectedConverter, setSelectedConverter] = useState({
    name: "",
    schema: {},
  });

  const getListOfConverters = useCallback(async () => {
    setLoading(true);
    try {
      const converters = await getComponentsRequest({
        selectTypes: ["Converter"],
      });
      setConverters(converters);
    } catch (error) {
      enqueueSnackbar("Error while trying to obtain list of converters");
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
    getListOfConverters();
  }, []);

  const handleAddConverter = () => {
    setConvertersToApply((prev) => [
      ...prev,
      {
        id: uuid(),
        order: prev.length + 1,
        name: selectedConverter.name,
        schema: selectedConverter.schema,
        params: {},
        scope: {
          columns: [],
          rows: [],
        },
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
            value={selectedConverter.name}
            onChange={(event) => {
              let converter = converters.find(
                (c) => c.name === event.target.value,
              );
              setSelectedConverter(converter);
            }}
            disabled={loading}
            InputProps={{
              endAdornment:
                selectedConverter.name != "" ? (
                  <InputAdornment
                    position="end"
                    sx={{
                      marginRight: 4,
                    }}
                  >
                    <Tooltip
                      title={selectedConverter.description}
                      placement="top"
                    >
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
          <Button
            onClick={() => handleAddConverter()}
            autoFocus
            fullWidth
            variant="outlined"
            color="primary"
            key="edit-button"
            startIcon={<AddIcon />}
            disabled={!selectedConverter.name}
            sx={{
              height: "100%",
            }}
          >
            Add
          </Button>
        </Grid>
      </Grid>
    </Grid>
  );
};

ConverterSelector.propTypes = {
  setConvertersToApply: PropTypes.func.isRequired,
};

export default ConverterSelector;
