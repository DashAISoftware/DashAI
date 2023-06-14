export function getRunStatus(statusNumber) {
  switch (statusNumber) {
    case 0:
      return "Not Started";
    case 1:
      return "Started";
    case 2:
      return "Finished";
    case 3:
      return "Error";
    default:
      throw new Error(`Error ${statusNumber} is not a valid status`);
  }
}
