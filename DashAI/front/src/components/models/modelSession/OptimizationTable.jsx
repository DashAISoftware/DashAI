import { Box, Grid, Paper, Typography } from "@mui/material";
import {
  MaterialReactTable,
  useMaterialReactTable,
} from "material-react-table";
import { useTheme } from "@mui/material/styles";
import PropTypes from "prop-types";
import React, { useEffect, useMemo, useState } from "react";
import EditOptimizerDialog from "./EditOptimizerDialog";
import OptimizationTableSelectOptimizer from "./OptimizationTableSelectOptimizer";
import { checkIfHaveOptimazers } from "../../utils/schema";
import { getComponents } from "../../api/component";
import { useTranslation } from "react-i18next";
import { useTableLocalization } from "../../../utils/useTableLocalization";

/**
 * This component renders a table to display the models that are currently in the experiment
 * @param {object} newExp object that contains the Experiment Modal state
 * @param {function} setNewExp updates the Eperimento Modal state (newExp)
 */
function OptimizationTable({ newExp, setNewExp }) {
  const [selectedOptimizer, setSelectedOptimizer] = useState({});
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

  const handleUpdateParameters = (id) => (newValues) => {
    setNewExp((prevExp) => {
      return {
        ...prevExp,
        runs: prevExp.runs.map((run) => {
          if (run.id === id) {
            return {
              ...run,
              optimizer_name: newExp.runs.find((r) => r.id === id)
                .optimizer_name,
              optimizer_parameters: newValues,
            };
          }
          return run;
        }),
      };
    });
  };

  const handleAddOptimizer = async (name, defaultValues, id) => {
    // sets the default values of the newly added optimizer, making optional the parameter configuration

    const optimizerRun = newExp.runs.map((run) => {
      if (run.id === id) {
        return {
          ...run,
          optimizer_name: name,
          optimizer_parameters: defaultValues,
        };
      }
      return run;
    });

    setNewExp((prevExp) => {
      return {
        ...prevExp,
        runs: optimizerRun,
      };
    });
  };

  const handleSelectedOptimizer = async (name, defaultValues, id) => {
    setSelectedOptimizer((prevSelectedOptimizer) => {
      return {
        ...prevSelectedOptimizer,
        [id]: name,
      };
    });

    handleAddOptimizer(name, defaultValues, id);
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
        id: "optimizer",
        header: t("experiments:label.configureOptimizer"),
        enableSorting: false,
        enableColumnFilter: false,
        Cell: ({ row }) => (
          <OptimizationTableSelectOptimizer
            taskName={newExp.task_name}
            optimizerName={row.original.optimizer_name}
            handleSelectedOptimizer={(optimizerName, defaultValues) =>
              handleSelectedOptimizer(
                optimizerName,
                defaultValues,
                row.original.id,
              )
            }
            variant="standard"
          />
        ),
      },
      {
        id: "actions",
        header: t("common:actions"),
        enableSorting: false,
        enableColumnFilter: false,
        Cell: ({ row }) => {
          if (!row.original.optimizer_name) {
            return null;
          }

          return (
            <Box sx={{ display: "flex", gap: 1 }}>
              <EditOptimizerDialog
                optimizerToConfigure={row.original.optimizer_name}
                updateParameters={handleUpdateParameters(row.original.id)}
                paramsInitialValues={row.original.optimizer_parameters}
              />
            </Box>
          );
        },
      },
    ],
    [models, newExp, t],
  );

  const table = useMaterialReactTable({
    columns,
    data: newExp.runs.filter(checkIfHaveOptimazers),
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

OptimizationTable.propTypes = {
  newExp: PropTypes.shape({
    id: PropTypes.string,
    name: PropTypes.string,
    dataset: PropTypes.object,
    task_name: PropTypes.string,
    step: PropTypes.string,
    created: PropTypes.instanceOf(Date),
    last_modified: PropTypes.instanceOf(Date),
    runs: PropTypes.array,
  }),
  setNewExp: PropTypes.func.isRequired,
};

export default OptimizationTable;
