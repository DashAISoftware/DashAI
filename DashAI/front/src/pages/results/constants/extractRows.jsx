// name of the properties in the run object that contain objects
const runObjectProperties = [
    "train_metrics",
    "test_metrics",
    "validation_metrics",
    "parameters",
  ];
  
  // function to get prefixes for the column names of each metric
  const getPrefix = (property) => {
    switch (property) {
      case "train_metrics":
        return "train_";
      case "test_metrics":
        return "test_";
      case "validation_metrics":
        return "val_";
      default:
        return "";
    }
  };

  export const extractRows = (rawRuns) => {
    let rows = [];
    rawRuns.forEach((run) => {
      let newRun = { ...run };
      runObjectProperties.forEach((p) => {
        // adds its corresponding prefix to the metric name (e.g. train_F1) and
        // if the metric value is a number, it is rounded to two decimal places.
        Object.keys(run[p] ?? {}).forEach((metric) => {
          newRun = {
            ...newRun,
            [`${getPrefix(p)}${metric}`]:
              typeof run[p][metric] === "number"
                ? run[p][metric].toFixed(2)
                : run[p][metric],
          };
        });
      });
      rows = [...rows, newRun];
    });
    return rows;
  };