const TOOL_TOUR_ATTRIBUTES = {
  HistogramPlotExplorer: "histogram-explorer",
  LabelEncoder: "label-encoder-converter",
  NanRemover: "nan-remover-converter",
};

export const getToolTourAttribute = (tool) => TOOL_TOUR_ATTRIBUTES[tool?.name];

export const isToolTourStep = (tourContext, tool) => {
  const attribute = getToolTourAttribute(tool);
  if (!tourContext?.run || !attribute) return false;
  const currentTarget = tourContext.steps?.[tourContext.stepIndex]?.target;
  return currentTarget === `[data-tour="${attribute}"]`;
};
