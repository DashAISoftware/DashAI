import { createReport } from "../../api/report";
import { enqueueReportJob } from "../../api/job";
import { startJobPolling } from "../../utils/jobPoller";

const SNACKBAR_AUTO_HIDE_MS = 5000;

/**
 * True when a report has parameters worth asking the user about.
 *
 * The component list already carries each schema, so this needs no request:
 * a report with no properties has nothing to configure and can be added on
 * the click itself rather than through a dialog with one button.
 *
 * @param {object} component  A report component as listed by getComponents.
 * @returns {boolean}
 */
export function hasConfigurableParameters(component) {
  return Object.keys(component?.schema?.properties ?? {}).length > 0;
}

/**
 * Create a report and enqueue its job, reporting both outcomes to the user.
 *
 * Shared so adding a report straight from the sidebar and adding one through
 * the parameter dialog behave identically.
 *
 * @param {object}   options
 * @param {number}   options.runId
 * @param {string}   options.reportName
 * @param {object}   [options.parameters]
 * @param {function} options.t                translation function
 * @param {function} options.enqueueSnackbar  notistack enqueue
 * @param {function} [options.onCreated]      called on create and on job end
 * @returns {Promise<object>} the created report row
 */
export async function createAndRunReport({
  runId,
  reportName,
  parameters = {},
  t,
  enqueueSnackbar,
  onCreated,
}) {
  const created = await createReport(runId, reportName, parameters);
  const job = await enqueueReportJob(created.id);

  enqueueSnackbar(t("reports:message.created"), {
    variant: "success",
    autoHideDuration: SNACKBAR_AUTO_HIDE_MS,
  });

  if (job && job.id) {
    startJobPolling(
      job.id,
      () => {
        if (onCreated) onCreated();
      },
      (result) => {
        console.error("Report job failed:", result);
        enqueueSnackbar(t("reports:message.failed"), {
          variant: "error",
          autoHideDuration: SNACKBAR_AUTO_HIDE_MS,
        });
        if (onCreated) onCreated();
      },
    );
  }

  // Fires before the job finishes so the card shows up computing rather than
  // appearing only once the work is done.
  if (onCreated) onCreated();
  return created;
}
