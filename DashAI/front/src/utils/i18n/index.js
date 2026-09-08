import i18n from "i18next";
import { initReactI18next } from "react-i18next";
import LanguageDetector from "i18next-browser-languagedetector";
import configurableObjectEN from "./locales/en/configurableObject.json";
import configurableObjectES from "./locales/es/configurableObject.json";
import commonEN from "./locales/en/common.json";
import commonES from "./locales/es/common.json";
import customEN from "./locales/en/custom.json";
import customES from "./locales/es/custom.json";
import experimentsEN from "./locales/en/experiments.json";
import experimentsES from "./locales/es/experiments.json";
import explainersEN from "./locales/en/explainers.json";
import explainersES from "./locales/es/explainers.json";
import generativeEN from "./locales/en/generative.json";
import generativeES from "./locales/es/generative.json";
import modelsEN from "./locales/en/models.json";
import modelsES from "./locales/es/models.json";
import datasetsEN from "./locales/en/datasets.json";
import datasetsES from "./locales/es/datasets.json";
import predictionEN from "./locales/en/prediction.json";
import predictionES from "./locales/es/prediction.json";
import homeTourEN from "./locales/en/homeTour.json";
import homeTourES from "./locales/es/homeTour.json";
import datasetsTourEN from "./locales/en/datasetsTour.json";
import datasetsTourES from "./locales/es/datasetsTour.json";
import notebookTourEN from "./locales/en/notebookTour.json";
import notebookTourES from "./locales/es/notebookTour.json";
import modelsTourEN from "./locales/en/modelsTour.json";
import modelsTourES from "./locales/es/modelsTour.json";
import modelsSessionTourEN from "./locales/en/modelsSessionTour.json";
import modelsSessionTourES from "./locales/es/modelsSessionTour.json";
import homeEN from "./locales/en/home.json";
import homeES from "./locales/es/home.json";
import pluginsEN from "./locales/en/plugins.json";
import pluginsES from "./locales/es/plugins.json";
import generativeTourEN from "./locales/en/generativeTour.json";
import generativeTourES from "./locales/es/generativeTour.json";
import hubEN from "./locales/en/hub.json";
import hubES from "./locales/es/hub.json";
import credentialsEN from "./locales/en/credentials.json";
import credentialsES from "./locales/es/credentials.json";
import credentialsPT from "./locales/pt/credentials.json";
import credentialsDE from "./locales/de/credentials.json";
import credentialsZH from "./locales/zh/credentials.json";
import configurableObjectPT from "./locales/pt/configurableObject.json";
import commonPT from "./locales/pt/common.json";
import customPT from "./locales/pt/custom.json";
import experimentsPT from "./locales/pt/experiments.json";
import explainersPT from "./locales/pt/explainers.json";
import generativePT from "./locales/pt/generative.json";
import modelsPT from "./locales/pt/models.json";
import datasetsPT from "./locales/pt/datasets.json";
import predictionPT from "./locales/pt/prediction.json";
import homeTourPT from "./locales/pt/homeTour.json";
import datasetsTourPT from "./locales/pt/datasetsTour.json";
import notebookTourPT from "./locales/pt/notebookTour.json";
import modelsTourPT from "./locales/pt/modelsTour.json";
import modelsSessionTourPT from "./locales/pt/modelsSessionTour.json";
import homePT from "./locales/pt/home.json";
import pluginsPT from "./locales/pt/plugins.json";
import generativeTourPT from "./locales/pt/generativeTour.json";
import configurableObjectDE from "./locales/de/configurableObject.json";
import commonDE from "./locales/de/common.json";
import customDE from "./locales/de/custom.json";
import experimentsDE from "./locales/de/experiments.json";
import explainersDE from "./locales/de/explainers.json";
import generativeDE from "./locales/de/generative.json";
import modelsDE from "./locales/de/models.json";
import datasetsDE from "./locales/de/datasets.json";
import predictionDE from "./locales/de/prediction.json";
import homeTourDE from "./locales/de/homeTour.json";
import datasetsTourDE from "./locales/de/datasetsTour.json";
import notebookTourDE from "./locales/de/notebookTour.json";
import modelsTourDE from "./locales/de/modelsTour.json";
import modelsSessionTourDE from "./locales/de/modelsSessionTour.json";
import homeDE from "./locales/de/home.json";
import pluginsDE from "./locales/de/plugins.json";
import generativeTourDE from "./locales/de/generativeTour.json";
import configurableObjectZH from "./locales/zh/configurableObject.json";
import commonZH from "./locales/zh/common.json";
import customZH from "./locales/zh/custom.json";
import experimentsZH from "./locales/zh/experiments.json";
import explainersZH from "./locales/zh/explainers.json";
import generativeZH from "./locales/zh/generative.json";
import modelsZH from "./locales/zh/models.json";
import datasetsZH from "./locales/zh/datasets.json";
import predictionZH from "./locales/zh/prediction.json";
import homeTourZH from "./locales/zh/homeTour.json";
import datasetsTourZH from "./locales/zh/datasetsTour.json";
import notebookTourZH from "./locales/zh/notebookTour.json";
import modelsTourZH from "./locales/zh/modelsTour.json";
import modelsSessionTourZH from "./locales/zh/modelsSessionTour.json";
import homeZH from "./locales/zh/home.json";
import pluginsZH from "./locales/zh/plugins.json";
import generativeTourZH from "./locales/zh/generativeTour.json";
import hubZH from "./locales/zh/hub.json";

// the translations
// (tip move them in a JSON file and import them,
// or even better, manage them separated from your code: https://react.i18next.com/guides/multiple-translation-files)
const resources = {
  en: {
    configurableObject: configurableObjectEN,
    common: commonEN,
    custom: customEN,
    experiments: experimentsEN,
    explainers: explainersEN,
    generative: generativeEN,
    models: modelsEN,
    datasets: datasetsEN,
    prediction: predictionEN,
    plugins: pluginsEN,
    home: homeEN,
    homeTour: homeTourEN,
    datasetsTour: datasetsTourEN,
    notebookTour: notebookTourEN,
    modelsTour: modelsTourEN,
    modelsSessionTour: modelsSessionTourEN,
    generativeTour: generativeTourEN,
    hub: hubEN,
    credentials: credentialsEN,
  },
  es: {
    configurableObject: configurableObjectES,
    common: commonES,
    custom: customES,
    experiments: experimentsES,
    explainers: explainersES,
    generative: generativeES,
    models: modelsES,
    datasets: datasetsES,
    prediction: predictionES,
    plugins: pluginsES,
    home: homeES,
    homeTour: homeTourES,
    datasetsTour: datasetsTourES,
    notebookTour: notebookTourES,
    modelsTour: modelsTourES,
    modelsSessionTour: modelsSessionTourES,
    generativeTour: generativeTourES,
    hub: hubES,
    credentials: credentialsES,
  },
  pt: {
    configurableObject: configurableObjectPT,
    common: commonPT,
    custom: customPT,
    experiments: experimentsPT,
    explainers: explainersPT,
    generative: generativePT,
    models: modelsPT,
    datasets: datasetsPT,
    prediction: predictionPT,
    plugins: pluginsPT,
    home: homePT,
    homeTour: homeTourPT,
    datasetsTour: datasetsTourPT,
    notebookTour: notebookTourPT,
    modelsTour: modelsTourPT,
    modelsSessionTour: modelsSessionTourPT,
    generativeTour: generativeTourPT,
    credentials: credentialsPT,
  },
  de: {
    configurableObject: configurableObjectDE,
    common: commonDE,
    custom: customDE,
    experiments: experimentsDE,
    explainers: explainersDE,
    generative: generativeDE,
    models: modelsDE,
    datasets: datasetsDE,
    prediction: predictionDE,
    plugins: pluginsDE,
    home: homeDE,
    homeTour: homeTourDE,
    datasetsTour: datasetsTourDE,
    notebookTour: notebookTourDE,
    modelsTour: modelsTourDE,
    modelsSessionTour: modelsSessionTourDE,
    generativeTour: generativeTourDE,
    credentials: credentialsDE,
  },
  zh: {
    configurableObject: configurableObjectZH,
    common: commonZH,
    custom: customZH,
    experiments: experimentsZH,
    explainers: explainersZH,
    generative: generativeZH,
    models: modelsZH,
    datasets: datasetsZH,
    prediction: predictionZH,
    plugins: pluginsZH,
    home: homeZH,
    homeTour: homeTourZH,
    datasetsTour: datasetsTourZH,
    notebookTour: notebookTourZH,
    modelsTour: modelsTourZH,
    modelsSessionTour: modelsSessionTourZH,
    generativeTour: generativeTourZH,
    hub: hubZH,
    credentials: credentialsZH,
  },
};

i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources,
    supportedLngs: ["en", "es", "pt", "de", "zh"],
    nonExplicitSupportedLngs: true,
    fallbackLng: "en",

    ns: [
      "common",
      "custom",
      "configurableObject",
      "experiments",
      "explainers",
      "generative",
      "models",
      "datasets",
      "prediction",
      "home",
      "homeTour",
      "datasetsTour",
      "notebookTour",
      "modelsTour",
      "modelsSessionTour",
      "plugins",
      "generativeTour",
      "hub",
      "credentials",
    ],
    defaultNS: "common",

    interpolation: {
      escapeValue: false,
    },
  });

export default i18n;
