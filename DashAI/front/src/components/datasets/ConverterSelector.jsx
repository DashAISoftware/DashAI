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
import ConverterEditorModal from "./ConverterEditorModal";
import { useSnackbar } from "notistack";
import { Help, AssignmentTurnedIn } from "@mui/icons-material";

import { getComponents as getComponentsRequest } from "../../api/component";
import uuid from "react-uuid";
import PropTypes from "prop-types";

const ConverterSelector = ({ datasetId, updateAppliedConvertersList }) => {
  const { enqueueSnackbar } = useSnackbar();
  const [loading, setLoading] = useState(true);
  const [converters, setConverters] = useState([]);

  const [newConverter, setNewConverter] = useState({
    name: "",
    schema: {},
  });

  const [openConverterEditor, setOpenConverterEditor] = useState(false);

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

  const handleClickOnSetButton = async () => {
    setOpenConverterEditor(true);
  };

  const handleAddConverter = (values) => {
    updateAppliedConvertersList((prev) => [
      ...prev,
      {
        id: uuid(),
        order: prev.length + 1,
        name: newConverter.name,
        schema: newConverter.schema,
        parameters: { ...values.params },
        scope: { ...values.scope },
      },
    ]);
  };

  const handleCloseConverterEditor = () => {
    setOpenConverterEditor(false);
    setNewConverter({
      name: "",
      schema: {},
    });
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
              endAdornment:
                newConverter.name !== "" ? (
                  <InputAdornment
                    position="end"
                    sx={{
                      marginRight: 4,
                    }}
                  >
                    {newConverter && (
                      <Tooltip
                        title={newConverter.schema.description}
                        placement="top"
                      >
                        <IconButton>
                          <Help />
                        </IconButton>
                      </Tooltip>
                    )}
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
            onClick={handleClickOnSetButton}
            autoFocus
            fullWidth
            variant="outlined"
            color="primary"
            key="edit-button"
            startIcon={<AssignmentTurnedIn />}
            disabled={!newConverter.name}
            sx={{
              height: "100%",
            }}
          >
            Set
          </Button>
        </Grid>
      </Grid>
      {/* Converter editor */}
      <ConverterEditorModal
        converterName={newConverter.name}
        updateValues={handleAddConverter}
        converterSchema={newConverter.schema}
        datasetId={datasetId}
        open={openConverterEditor}
        handleClose={handleCloseConverterEditor}
      />
    </Grid>
  );
};

ConverterSelector.propTypes = {
  datasetId: PropTypes.number.isRequired,
  updateAppliedConvertersList: PropTypes.func.isRequired,
};

export default ConverterSelector;