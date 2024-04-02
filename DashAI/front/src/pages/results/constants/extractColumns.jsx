import { actionsColumns } from "./actionsColumns";
import { initialColumns } from "./initialColumns";

export const extractColumns = (rawMetrics, rawRuns, handleRunResultsOpen) => {
    // extract metrics
    let metrics = [];
    for (const metric of rawMetrics) {
      metrics = [
        ...metrics,
        { field: `train_${metric.name}` },
        { field: `test_${metric.name}` },
        { field: `val_${metric.name}` },
      ];
    }

    // extract parameters
    let distinctParameters = {};
    for (const run of rawRuns) {
      distinctParameters = { ...distinctParameters, ...run.parameters };
    }
    const parameters = Object.keys(distinctParameters).map((name) => {
      return { field: name };
    });

    // column grouping
    const columnGroupingModel = [
      { groupId: "Info", children: [...initialColumns] },
      { groupId: "Metrics", children: [...metrics] },
      { groupId: "Parameters", children: [...parameters] },
    ];

    // column visibility
    let columnVisibilityModel = {
      created: false,
      last_modified: false,
      start_time: false,
      end_time: false,
    };
    [...metrics, ...parameters].forEach((col) => {
      if (col.field.includes("test")) {
        return; // skip this iteration and proceed with the next one
      }
      columnVisibilityModel = { ...columnVisibilityModel, [col.field]: false };
    });

    const columns = [
      ...actionsColumns(handleRunResultsOpen),
      ...initialColumns,
      ...metrics,
      ...parameters,
    ];

    return { columns, columnGroupingModel, columnVisibilityModel };
  };