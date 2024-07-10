import { MenuItem, TextField } from "@mui/material";
import React, { useState } from "react";
import useOptimizersByTask from "../../hooks/useOptimizersByTask";
import useSchemaWithCallback from "../../hooks/useSchemaWithCallback";

function OptimizationTableSelectOptimizer({
  taskName,
  optimizerName,
  handleSelectedOptimizer,
}) {
  const { compatibleModels } = useOptimizersByTask({ taskName });
  const [selectedOptimizer, setSelectedOptimizer] = useState(optimizerName);

  useSchemaWithCallback({ modelName: selectedOptimizer }, (defaultValues) => {
    if (
      selectedOptimizer &&
      defaultValues &&
      Object.keys(defaultValues).length > 0 &&
      selectedOptimizer !== optimizerName
    ) {
      handleSelectedOptimizer(selectedOptimizer, defaultValues);
    }
  });

  return (
    <>
      <TextField
        select
        label="Select an optimizer to add"
        value={selectedOptimizer || ""}
        onChange={(e) => {
          setSelectedOptimizer(e.target.value);
        }}
        fullWidth
      >
        {compatibleModels.map((optimizer) => (
          <MenuItem key={optimizer.name} value={optimizer.name}>
            {optimizer.name}
          </MenuItem>
        ))}
      </TextField>
    </>
  );
}

export default OptimizationTableSelectOptimizer;
