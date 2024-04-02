export const getDisplaySetName = (displaySet) => {
    switch (displaySet) {
      case "test_metrics":
        return "test";
      case "train_metrics":
        return "train";
      case "validation_metrics":
        return "validation";
      default:
        throw new Error(`Error, set name ${displaySet} is not recognized`);
    }
  };