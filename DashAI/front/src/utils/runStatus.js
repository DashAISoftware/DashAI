export function getRunStatus(statusNumber, t) {
  switch (statusNumber) {
    case 0:
      return t("common:notStarted");
    case 1:
      return t("common:delivered");
    case 2:
      return t("common:started");
    case 3:
      return t("common:finished");
    case 4:
      return t("common:error");
    default:
      throw new Error(`Error ${statusNumber} is not a valid status`);
  }
}

export function getRunStatusColor(statusNumber) {
  switch (statusNumber) {
    case 0:
      return "default";
    case 1:
    case 2:
      return "info";
    case 3:
      return "success";
    case 4:
      return "error";
    default:
      return "default";
  }
}

// Not Started, Finished, or Error — anything eligible for a (re)train action.
export function canTrainRun(statusNumber) {
  return statusNumber === 0 || statusNumber === 3 || statusNumber === 4;
}

// Delivered or Started — currently executing, nothing new can be triggered.
export function isRunActive(statusNumber) {
  return statusNumber === 1 || statusNumber === 2;
}
