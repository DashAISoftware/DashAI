import React, { useState, useEffect, useMemo } from "react";
import PropTypes from "prop-types";
import {
  MaterialReactTable,
  useMaterialReactTable,
} from "material-react-table";
import { useTheme } from "@mui/material/styles";
import { Box, Grid, Paper, Typography } from "@mui/material";
import DeleteItemModal from "../custom//DeleteItemModal";
import EditModelDialog from "./EditModelDialog";
import ModelsTableSelectMetric from "./ModelsTableSelectMetric";
import { checkIfHaveOptimazers } from "../../utils/schema";
import { getComponents } from "../../api/component";
import { useTranslation } from "react-i18next";
import { useTableLocalization } from "../../../utils/useTableLocalization";

/**
 * This component renders a table to display the models that are currently in the experiment
 * @param {object} newExp object that contains the Experiment Modal state
 * @param {function} setNewExp updates the Eperimento Modal state (newExp)
 */
function ModelsTable({ newExp, setNewExp }) {
  const [selectedMetric, setSelectedMetric] = useState({});
  const [models, setModels] = useState([]);
  const { t } = useTranslation(["experiments", "common"]);
  const theme = useTheme();
  const localization = useTableLocalization();

  useEffect(() => {
    const fetchModels = async () => {
      try {
        const response = await getComponents({ selectTypes: ["Model"] });
        setModels(response);
      } catch (error) {
        console.error("Error fetching models:", error);
      }
    };
    fetchModels();
  }, []);

  const handleDeleteModel = (id) => {
    setNewExp({
      ...newExp,
      runs: newExp.runs.filter((model) => model.id !== id),
    });
  };
  const handleUpdateParameters = (id) => (newValues) => {
    setNewExp((prevExp) => {
      return {
        ...prevExp,
        runs: prevExp.runs.map((model) => {
          if (model.id === id) {
            return {
              ...model,
              params: newValues,
              goal_metric: selectedMetric[id],
            };
          }
          return model;
        }),
      };
    });
  };

  const handleAddMetric = async (name, id) => {
    // sets the default values of the newly added optimizer, making optional the parameter configuration

    const metricRun = newExp.runs.map((run) => {
      if (run.id === id) {
        return {
          ...run,
          goal_metric: name,
        };
      }
      return run;
    });

    setNewExp((prevExp) => {
      return {
        ...prevExp,
        runs: metricRun,
      };
    });
  };

  const handleSelectedMetric = async (name, id) => {
    setSelectedMetric((prevSelectedMetric) => {
      return {
        ...prevSelectedMetric,
        [id]: name,
      };
    });

    handleAddMetric(name, id);
  };

  const columns = useMemo(
    () => [
      {
        accessorKey: "name",
        header: t("common:name"),
      },
      {
        accessorKey: "model",
        header: t("common:model"),
        accessorFn: (row) => {
          const model = models.find((m) => m.name === row.model);
          return model && model.display_name ? model.display_name : row.model;
        },
      },
      {
        id: "actions",
        header: t("common:actions"),
        enableSorting: false,
        enableColumnFilter: false,
        Cell: ({ row }) => (
          <Box sx={{ display: "flex", gap: 1 }}>
            <EditModelDialog
              modelToConfigure={row.original.model}
              updateParameters={handleUpdateParameters(row.original.id)}
              paramsInitialValues={row.original.params}
            />
            <DeleteItemModal
              deleteFromTable={() => handleDeleteModel(row.original.id)}
            />
          </Box>
        ),
      },
      {
        id: "metric",
        header: t("experiments:label.optimizerMetric"),
        enableSorting: false,
        enableColumnFilter: false,
        Cell: ({ row }) => {
          // Check if this specific row has optimizers
          const rowHasOptimizers = checkIfHaveOptimazers(row.original);

          // Only render the metric selector if the row has optimizers
          if (!rowHasOptimizers) {
            return (
              <Typography
                variant="body2"
                sx={{
                  color: "text.secondary",
                  fontStyle: "italic",
                }}
              >
                {t("experiments:label.noOptimizersNoMetric")}
              </Typography>
            );
          }

          return (
            <ModelsTableSelectMetric
              taskName={newExp.task_name}
              metricName={row.original.goal_metric}
              handleSelectedMetric={(metricName) =>
                handleSelectedMetric(metricName, row.original.id)
              }
              required
              variant="standard"
            />
          );
        },
      },
    ],
    [models, newExp, t],
  );

  const table = useMaterialReactTable({
    columns,
    data: newExp.runs,
    muiTableBodyCellProps: { sx: { whiteSpace: "pre" } },
    mrtTheme: { baseBackgroundColor: theme.palette.ui.panelDark },
    muiTablePaperProps: { elevation: 0 },
    localization,
    initialState: { density: "compact" },
    enableRowSelection: false,
  });

  return (
    <Paper sx={{ py: 4, px: 8 }}>
      {/* Title */}
      <Grid
        container
        direction="row"
        justifyContent="space-between"
        alignItems="center"
        sx={{ mb: 8 }}
      >
        <Typography variant="subtitle1" component="h3">
          {t("experiments:label.modelsInExperiment")}
        </Typography>
      </Grid>

      {/* Models Table */}
      <MaterialReactTable table={table} />
    </Paper>
  );
}

ModelsTable.propTypes = {
  newExp: PropTypes.shape({
    id: PropTypes.string,
    name: PropTypes.string,
    dataset: PropTypes.object,
    task_name: PropTypes.string,
    input_columns: PropTypes.arrayOf(PropTypes.string),
    output_columns: PropTypes.arrayOf(PropTypes.string),
    splits: PropTypes.shape({
      training: PropTypes.number,
      validation: PropTypes.number,
      testing: PropTypes.number,
    }),
    step: PropTypes.string,
    created: PropTypes.instanceOf(Date),
    last_modified: PropTypes.instanceOf(Date),
    runs: PropTypes.array,
  }),
  setNewExp: PropTypes.func.isRequired,
};

export default ModelsTable;
