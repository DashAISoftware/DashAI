import { Trans } from "react-i18next";

const tipStyle = {
  backgroundColor: "rgba(76, 175, 80, 0.12)",
  color: "inherit",
  padding: "8px",
  borderRadius: "4px",
  marginTop: "10px",
  borderLeft: "3px solid #43A047",
};

// `stage` is the HubImportPanel step the tour step lives on:
// 0 = file select, 1 = dataloader, 2 = preview. See useTourStageSync.
export const hubImportTourSteps = [
  {
    target: "body",
    content: (
      <Trans i18nKey="hubTour:importIntro">
        <div>
          <h3></h3>
          <p></p>
          <ol>
            <li></li>
            <li></li>
            <li></li>
          </ol>
        </div>
      </Trans>
    ),
    placement: "center",
    disableBeacon: true,
  },
  {
    target: '[data-tour="hub-example-file"]',
    content: (
      <Trans i18nKey="hubTour:selectFile">
        <div>
          <h3></h3>
          <p></p>
          <p>
            <strong></strong>
          </p>
        </div>
      </Trans>
    ),
    placement: "bottom",
    disableBeacon: true,
    spotlightClicks: true,
    hideFooter: true,
    isInteractive: true,
    stage: 0,
  },
  {
    target: '[data-tour="hub-datafile-info"]',
    content: (
      <Trans i18nKey="hubTour:datafileInfo">
        <div>
          <h3></h3>
          <p></p>
        </div>
      </Trans>
    ),
    placement: "left",
    disableBeacon: true,
    stage: 0,
  },
  {
    target: '[data-tour="hub-import-next-button"]',
    content: (
      <Trans i18nKey="hubTour:fileNext">
        <div>
          <h3></h3>
          <p></p>
        </div>
      </Trans>
    ),
    placement: "top",
    disableBeacon: true,
    spotlightClicks: true,
    hideFooter: true,
    isInteractive: true,
    stage: 0,
  },
  {
    target: '[data-tour="hub-example-dataloader-option"]',
    content: (
      <Trans i18nKey="hubTour:selectLoader">
        <div>
          <h3></h3>
          <p></p>
          <p></p>
          <p>
            <strong></strong>
          </p>
        </div>
      </Trans>
    ),
    placement: "right",
    disableBeacon: true,
    disableBackButton: true,
    spotlightClicks: true,
    hideFooter: true,
    isInteractive: true,
    stage: 1,
  },
  {
    target: '[data-tour="hub-import-next-button"]',
    content: (
      <Trans i18nKey="hubTour:loaderNext">
        <div>
          <h3></h3>
          <p></p>
        </div>
      </Trans>
    ),
    placement: "top",
    disableBeacon: true,
    spotlightClicks: true,
    hideFooter: true,
    isInteractive: true,
    stage: 1,
  },
  {
    target: '[data-tour="hub-preview-table"]',
    content: (
      <Trans i18nKey="hubTour:preview">
        <div>
          <h3></h3>
          <p></p>
          <p></p>
        </div>
      </Trans>
    ),
    placement: "top",
    disableBeacon: true,
    disableBackButton: true,
    spotlightClicks: true,
    stage: 2,
  },
  {
    target: '[data-tour="hub-dataset-name"]',
    content: (
      <Trans i18nKey="hubTour:datasetName">
        <div>
          <h3></h3>
          <p></p>
        </div>
      </Trans>
    ),
    placement: "bottom",
    disableBeacon: true,
    spotlightClicks: true,
    stage: 2,
  },
  {
    target: '[data-tour="dataloader-config"]',
    content: (
      <Trans i18nKey="hubTour:loaderConfig">
        <div>
          <h3></h3>
          <p></p>
          <p style={tipStyle}>
            <strong></strong>
          </p>
        </div>
      </Trans>
    ),
    placement: "left",
    disableBeacon: true,
    spotlightClicks: true,
    stage: 2,
  },
  {
    target: '[data-tour="hub-import-button"]',
    content: (
      <Trans i18nKey="hubTour:importDataset">
        <div>
          <h3></h3>
          <p>
            <strong></strong>
          </p>
          <p></p>
        </div>
      </Trans>
    ),
    placement: "top",
    disableBeacon: true,
    spotlightClicks: true,
    hideFooter: true,
    isInteractive: true,
    stage: 2,
  },
];

export const hubImportTourConfig = {
  continuous: true,
  showProgress: true,
  showSkipButton: true,
  showBackButton: true,
  disableOverlayClose: true,
  disableCloseOnEsc: false,
};
