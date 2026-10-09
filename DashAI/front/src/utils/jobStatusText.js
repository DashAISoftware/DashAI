const JOB_STATUS_TRANSLATION_KEYS = {
  not_started: "common:jobQueue.status.queued",
  started: "common:jobQueue.status.running",
  finished: "common:jobQueue.status.completed",
  error: "common:jobQueue.status.failed",
  deleted: "common:jobQueue.status.deleted",
  cancelled: "common:jobQueue.status.cancelled",
  killed: "common:jobQueue.status.killed",
};

/**
 * Returns the translated status label for a job.
 * @param {string} status - Job status string from the backend.
 * @param {function} t - i18next translation function.
 */
const getStatusText = (status, t) => {
  const key = status && JOB_STATUS_TRANSLATION_KEYS[status];
  if (key) {
    return t(key);
  }
  return status || t("common:unknown");
};

export { JOB_STATUS_TRANSLATION_KEYS, getStatusText };
