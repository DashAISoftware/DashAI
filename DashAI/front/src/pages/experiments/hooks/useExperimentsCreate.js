import { useSnackbar } from "notistack";
import { createExperiment as createExperimentRequest } from "../../../api/experiment";
import { createRun as createRunRequest } from "../../../api/run";

/*
 * Custom hook to create a new experiment
 * @param {object} newExp - object containing the new experiment information
 * @param {function} onSuccess - callback function to be called on successful fetch
 */

export default function useExperimentsCreate({ newExp, onSuccess }) {
  const { enqueueSnackbar } = useSnackbar();

  const uploadRuns = async (experimentId) => {
    for (const run of newExp.runs) {
      try {
        await createRunRequest(
          experimentId,
          run.model,
          run.name,
          run.params,
          "",
        );
      } catch (error) {
        enqueueSnackbar(`Error while trying to create a new run: ${run.name}`);

        if (error.response) {
          console.error("Response error:", error.message);
        } else if (error.request) {
          console.error("Request error", error.request);
        } else {
          console.error("Unknown Error", error.message);
        }
      }
    }
  };

  const uploadNewExperiment = async () => {
    try {
      const response = await createExperimentRequest(
        newExp.dataset.id,
        newExp.task_name,
        newExp.name,
      );

      const experimentId = response.id;
      await uploadRuns(experimentId);

      enqueueSnackbar("Experiment successfully created.", {
        variant: "success",
      });
      onSuccess && onSuccess();
    } catch (error) {
      enqueueSnackbar("Error while trying to create a new experiment");

      if (error.response) {
        console.error("Response error:", error.message);
      } else if (error.request) {
        console.error("Request error", error.request);
      } else {
        console.error("Unknown Error", error.message);
      }
    }
  };
  return { uploadNewExperiment };
}
