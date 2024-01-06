import { useSnackbar } from "notistack";
import React, { useState } from "react";
import DeleteItemModal from "../../../components/custom/DeleteItemModal";
import RunnerDialog from "../../../components/experiments/RunnerDialog";
import { initialColumns } from "../constants";
import useExperiments from "./useExperiments";
import useExperimentsDelete from "./useExperimentsDelete";

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
    ...initialColumns,
    {
      field: "actions",
      type: "actions",
      minWidth: 80,
      getActions: (params) => [
        <RunnerDialog
          key="runner-dialog"
          experiment={params.row}
          expRunning={expRunning}
          setExpRunning={setExpRunning}
        />,
        <DeleteItemModal
          key="delete-button"
          deleteFromTable={() => deleteExperiment(params.id)}
        />,
      ],
    },
  ];

  return {
    rows,
    columns,
    loading: loading || deleteLoading,
  };
}
