import { useSnackbar } from "notistack";
import React, { useState } from "react";
import DeleteItemModal from "../../../components/custom/DeleteItemModal";
import ExperimentsRunnerDialog from "../components/ExperimentsRunnerDialog";
import { experimentsColumns } from "../constants/table";
import useExperiments from "./useExperiments";
import useExperimentsDelete from "./useExperimentsDelete";

/*
 * Custom hook to build rows and columns for the experiments table
 * @param {boolean} updateTableFlag - boolean to indicate whether to refresh the experiments
 * @param {function} setUpdateTableFlag - function to set the updateTableFlag
 */

export default function useExperimentsTable({
  updateTableFlag,
  setUpdateTableFlag,
}) {
  const [expRunning, setExpRunning] = useState({});
  const { enqueueSnackbar } = useSnackbar();

  const { experiments: rows, loading } = useExperiments({
    onSuccess: (initialState) => setExpRunning(initialState),
    onError: () =>
      enqueueSnackbar("Error while trying to obtain the experiment table."),
    onSettled: () => setUpdateTableFlag(false),
    refresh: updateTableFlag,
  });

  const { deleteExperiment, loading: deleteLoading } = useExperimentsDelete({
    onSuccess: () => {
      setUpdateTableFlag(true);
      enqueueSnackbar("Experiment deleted successfully.");
    },
    onError: () =>
      enqueueSnackbar("Error while trying to delete the experiment."),
  });
  const columns = [
    ...experimentsColumns,
    {
      field: "actions",
      type: "actions",
      minWidth: 80,
      getActions: (params) => {
        return [
          <ExperimentsRunnerDialog
            key="runner-dialog"
            experiment={params.row}
            expRunning={expRunning}
            setExpRunning={setExpRunning}
          />,
          <DeleteItemModal
            key="delete-button"
            deleteFromTable={() => deleteExperiment(params.id)}
          />,
        ];
      },
    },
  ];

  return {
    rows,
    columns,
    loading: loading || deleteLoading,
  };
}
