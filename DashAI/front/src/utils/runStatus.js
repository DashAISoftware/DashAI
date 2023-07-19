export function getRunStatus(statusNumber) {
  switch (statusNumber) {
    case 0:
      return "Not Started";
    case 1:
      return "Delivered";
    case 2:
      return "Started";
    case 3:
      return "Finished";
    case 4:
      return "Error";
    default:
      throw new Error(`Error ${statusNumber} is not a valid status`);
  }
}
