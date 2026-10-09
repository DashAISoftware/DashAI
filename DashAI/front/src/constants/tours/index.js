import { homeTourSteps, homeTourConfig } from "./homeTour";
import { datasetsTourSteps, datasetsTourConfig } from "./datasetsTour";
import { datasetViewTourSteps, datasetViewTourConfig } from "./datasetViewTour";
import { notebookTourSteps, notebookTourConfig } from "./notebookTour";
import { modelsTourSteps, modelsTourConfig } from "./modelsTour";
import {
  modelsSessionTourSteps,
  modelsSessionTourConfig,
} from "./modelsSessionTour";
import { generativeTourSteps, generativeTourConfig } from "./generativeTour";
import { hubTourSteps, hubTourConfig } from "./hubTour";
import { hubImportTourSteps, hubImportTourConfig } from "./hubImportTour";

export const tours = {
  home: {
    steps: homeTourSteps,
    config: homeTourConfig,
  },
  datasets: {
    steps: datasetsTourSteps,
    config: datasetsTourConfig,
  },
  datasetView: {
    steps: datasetViewTourSteps,
    config: datasetViewTourConfig,
  },
  notebook: {
    steps: notebookTourSteps,
    config: notebookTourConfig,
  },
  models: {
    steps: modelsTourSteps,
    config: modelsTourConfig,
  },
  modelsSession: {
    steps: modelsSessionTourSteps,
    config: modelsSessionTourConfig,
  },
  generative: {
    steps: generativeTourSteps,
    config: generativeTourConfig,
  },
  hub: {
    steps: hubTourSteps,
    config: hubTourConfig,
  },
  hubImport: {
    steps: hubImportTourSteps,
    config: hubImportTourConfig,
  },
};

export const TOUR_KEYS = {
  HOME: "home",
  DATASETS: "datasets",
  DATASET_VIEW: "datasetView",
  NOTEBOOK: "notebook",
  MODELS: "models",
  MODELS_SESSION: "modelsSession",
  GENERATIVE: "generative",
  HUB: "hub",
  HUB_IMPORT: "hubImport",
};
