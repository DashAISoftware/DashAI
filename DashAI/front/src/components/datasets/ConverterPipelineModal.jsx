import React, { useEffect, useState } from "react";
import { GridActionsCellItem } from "@mui/x-data-grid";
import PropTypes from "prop-types";
import {
  Box,
  IconButton,
  Typography,
  Button,
  ButtonGroup,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  TextField,
  Stack,
  DialogContentText,
  MenuItem,
  FormControl,
  InputLabel,
  Select,
  OutlinedInput,
} from "@mui/material";
import { ArrowBackOutlined, Cable } from "@mui/icons-material";
import uuid from "react-uuid";

const ConverterPipelineModal = ({
  converters,
  setConvertersToApply,
  existingPipelines,
  setExistingPipelines,
  converterToAdd,
}) => {
  const [open, setOpen] = useState(false);
  const [selectedPipeline, setSelectedPipeline] = useState({
    name: "",
    id: "",
    scope: {
      columns: [],
      rows: [],
    },
    order: 0,
  });

  const handleOnChange = (event) => {
    if (event.target.value === "new-pipeline") {
      setSelectedPipeline({
        name: "",
        id: "new-pipeline",
        scope: converterToAdd.scope,
        order: converterToAdd.order, // It takes the order of the converter, which will make room for the new pipeline
      });
      return;
    }
    if (event.target.value === "no-pipeline") {
      setSelectedPipeline({
        name: "",
        id: "no-pipeline",
        scope: {
          columns: [],
          rows: [],
        },
        order: 0,
      });
      return;
    }
    const pipeline = existingPipelines.find((p) => p.id === event.target.value);
    setSelectedPipeline(pipeline);
  };

  const deletePipeline = (pipelineId) => {
    setExistingPipelines((prev) => prev.filter((p) => p.id !== pipelineId));
  };

  const updatePipelineOrder = (pipelineId, order) => {
    setExistingPipelines((prev) => {
      const pipelineList = [...prev];
      let pipelineIndex = pipelineList.findIndex(
        (pipeline) => pipeline.id === pipelineId,
      );
      pipelineList[pipelineIndex] = {
        ...pipelineList[pipelineIndex],
        order: order,
      };
      return pipelineList;
    });
  };

  const handleAddToNewPipeline = () => {
    // Get name of the last pipeline created so the new pipeline can be named accordingly
    let lastPipeline = existingPipelines[existingPipelines.length - 1];
    let newPipelineIndex = lastPipeline
      ? parseInt(lastPipeline.name.split(" ")[1]) + 1
      : 1;
    const pipelineId = uuid();
    let pipelineToAssign = {
      name: `Pipeline ${newPipelineIndex}`,
      id: pipelineId, // Generate a unique id for the pipeline
      scope: converterToAdd.scope, // It takes the scope of the converter
      order: converterToAdd.order, // It takes the order of the converter, which will make room for the new pipeline
    };
    setExistingPipelines((prev) => [...prev, pipelineToAssign]);

    setConvertersToApply((prev) =>
      prev.map((converter) => {
        if (converter.id === converterToAdd.id) {
          return {
            ...converter,
            pipelineId: pipelineId,
            scope: converterToAdd.scope,
            order: converterToAdd.order + 1, // Make room for the new pipeline
          };
        } else if (converter.order > converterToAdd.order) {
          // Update the order of the converters that come after the new pipeline
          return {
            ...converter,
            order: converter.order + 1,
          };
        }
        return converter;
      }),
    );
  };

  const handleAddToExistingPipeline = (pipelineToAssign) => {
    // If the converter is being moved to a pipeline that comes before it
    if (converterToAdd.order < pipelineToAssign.order) {
      // Update the order of the pipeline and its converters that come after it,
      // since this new converter will go to the end of the pipeline
      updatePipelineOrder(pipelineToAssign.id, pipelineToAssign.order - 1);

      setConvertersToApply((prev) =>
        prev.map((converter) => {
          if (converter.id !== converterToAdd.id) {
            if (
              converter.pipelineId === pipelineToAssign.id &&
              converter.order > converterToAdd.order
            ) {
              return {
                ...converter,
                order: converter.order - 1,
              };
            }
            // If this converter is not in the same pipeline, do nothing
            return converter;
          } else {
            let lastConverterInThisPipeline = prev.findLast(
              (converter) => converter.pipelineId === pipelineToAssign.id,
            );
            return {
              ...converter,
              pipelineId: pipelineToAssign.id,
              scope: pipelineToAssign.scope,
              order: lastConverterInThisPipeline.order, // Take the place of the converter that was moved
            };
          }
        }),
      );
    } else {
      // Otherwise, just add the converter to the end of the pipeline
      setConvertersToApply((prev) =>
        prev.map((converter) => {
          if (converter.id !== converterToAdd.id) {
            return converter;
          } else {
            let lastConverterInThisPipeline = prev.findLast(
              (converter) => converter.pipelineId === pipelineToAssign.id,
            );
            return {
              ...converter,
              pipelineId: pipelineToAssign.id,
              scope: pipelineToAssign.scope,
              order: lastConverterInThisPipeline.order + 1, // Add the converter to the end of the pipeline
            };
          }
        }),
      );
    }
  };

  const handleRemoveFromPipeline = (pipelineIdToRemove) => {
    // Check if pipeline has only one converter, if so, delete the pipeline
    let pipelineToDelete = converters.filter(
      (converter) => converter.pipelineId === pipelineIdToRemove,
    );
    if (pipelineToDelete.length === 1) {
      deletePipeline(pipelineIdToRemove);
      setConvertersToApply((prev) =>
        prev.map((converter) => {
          if (converter.id === converterToAdd.id) {
            return {
              ...converter,
              pipelineId: null,
              order: converterToAdd.order - 1, // Take the place of the pipeline
            };
          }
          if (converter.order > converterToAdd.order) {
            // Update the order of the converters that come after the pipeline
            return {
              ...converter,
              order: converter.order - 1,
            };
          }
          return converter;
        }),
      );
    }
    // Otherwise, move the converter out of the pipeline
    else {
      setConvertersToApply((prev) =>
        prev.map((converter) => {
          if (converter.id !== converterToAdd.id) {
            // If this converter is in the same pipeline
            // and it comes after the converter to remove, update its order
            if (
              converter.pipelineId === pipelineIdToRemove &&
              converter.order > converterToAdd.order
            ) {
              return {
                ...converter,
                order: converter.order - 1,
              };
            }
            // If this converter comes before the converter to remove
            // or it is not in the same pipeline, do nothing
            return converter;
          } else {
            // If this converter is the one to remove
            let lastConverterInThisPipeline = prev.findLast(
              (converter) =>
                converter.pipelineId === pipelineIdToRemove &&
                converter.id !== converterToAdd.id,
            );
            return {
              ...converter,
              pipelineId: null,
              scope: {
                columns: [],
                rows: [],
              }, // Reset the scope
              order: lastConverterInThisPipeline.order + 1, // Move the converter out of the pipeline
            };
          }
        }),
      );
    }
  };

  const handleOnSave = () => {
    if (selectedPipeline.id === "new-pipeline") {
      handleAddToNewPipeline();
    } else if (selectedPipeline.id === "no-pipeline") {
      handleRemoveFromPipeline(converterToAdd.pipelineId);
    } else {
      handleAddToExistingPipeline(selectedPipeline);
    }

    setOpen(false);
  };

  //   useEffect(() => {
  //     setSelectedPipeline(
  //       converterToAdd.pipelineName
  //         ? {
  //             name: converterToAdd.pipelineName,
  //             scope: converterToAdd.scope,
  //           }
  //         : {
  //             name: "",
  //             scope: {
  //               columns: [],
  //               rows: [],
  //             },
  //           },
  //     );
  //     return () => {
  //       setSelectedPipeline({
  //         name: "",
  //         scope: {
  //           columns: [],
  //           rows: [],
  //         },
  //       });
  //     };
  //   }, [open]);

  return (
    <React.Fragment>
      <GridActionsCellItem
        key="manage-pipeline-button"
        icon={<Cable />}
        label="Manage pipeline"
        onClick={() => setOpen(true)}
      >
        Manage pipeline
      </GridActionsCellItem>
      <Dialog open={open} onClose={() => setOpen(false)}>
        <DialogTitle>
          <Box display="flex" alignItems="center">
            <IconButton onClick={() => setOpen(false)}>
              <ArrowBackOutlined />
            </IconButton>
            <Typography variant="h5" sx={{ ml: 2 }}>
              Manage pipeline
            </Typography>
          </Box>
        </DialogTitle>
        <DialogContent>
          <Stack spacing={4} sx={{ py: 2 }} transition="ease">
            <DialogContentText>
              A Pipeline applies a sequence of converters to preprocess data,
              passing the output of one converter to the next, with its scope
              defined by the first converter.
            </DialogContentText>
            <TextField
              select
              value={selectedPipeline.id}
              onChange={handleOnChange}
              fullWidth
              label="Select pipeline"
            >
              {existingPipelines.map((pipeline) => (
                <MenuItem divider key={pipeline.id} value={pipeline.id}>
                  {pipeline.name}
                </MenuItem>
              ))}

              {!converterToAdd.pipelineId && (
                <MenuItem value="new-pipeline">Create new pipeline</MenuItem>
              )}
              {converterToAdd.pipelineId && (
                <MenuItem value="no-pipeline">Remove from pipeline</MenuItem>
              )}
            </TextField>
          </Stack>
        </DialogContent>
        <DialogActions>
          <ButtonGroup>
            <Button onClick={() => setOpen(false)}>Back</Button>
            <Button variant="contained" onClick={handleOnSave}>
              Save
            </Button>
          </ButtonGroup>
        </DialogActions>
      </Dialog>
    </React.Fragment>
  );
};

export default ConverterPipelineModal;
