import { Box, Button, MenuItem, TextField } from "@mui/material";
import React, { useState } from "react";
import { AddCircleOutline as AddIcon } from "@mui/icons-material";
import PropTypes from "prop-types";

function ExperimentsCreateModelsToolbar({
  selectedModel,
  setSelectedModel,
  compatibleModels,
  handleAddButton,
}) {
  const [name, setName] = useState("");

  return (
    <Box display="flex" gap={2}>
      <Box flex={1}>
        <TextField
          label="Name (optional)"
          value={name}
          onChange={(e) => setName(e.target.value)}
          fullWidth
        />
      </Box>
      <Box flex={1}>
        <TextField
          select
          label="Select a model to add"
          value={selectedModel}
          onChange={(e) => {
            setSelectedModel(e.target.value);
          }}
          fullWidth
        >
          {compatibleModels.map((model) => (
            <MenuItem key={model.name} value={model.name}>
              {model.name}
            </MenuItem>
          ))}
        </TextField>
      </Box>
      <Box>
        {" "}
        <Button
          variant="outlined"
          disabled={selectedModel === ""}
          startIcon={<AddIcon />}
          onClick={() => handleAddButton({ onSuccess: () => setName("") })}
          sx={{ height: "100%" }}
        >
          Add
        </Button>
      </Box>
    </Box>
  );
}

ExperimentsCreateModelsToolbar.propTypes = {
  selectedModel: PropTypes.string,
  setSelectedModel: PropTypes.func,
  compatibleModels: PropTypes.array,
  setName: PropTypes.func,
  handleAddButton: PropTypes.func,
};

export default ExperimentsCreateModelsToolbar;
