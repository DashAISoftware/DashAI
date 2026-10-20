import { Trans } from "react-i18next";

const tipStyle = {
  backgroundColor: "rgba(76, 175, 80, 0.12)",
  color: "inherit",
  padding: "8px",
  borderRadius: "4px",
  marginTop: "10px",
  borderLeft: "3px solid #43A047",
};

// `stage` ties a step to the screen it lives on: "source" is the source
// picker (/app/data/hub), "grid" the dataset browser (/app/data/hub/:source).
// See useTourStageSync.
export const hubTourSteps = [
  {
    target: "body",
    content: (
      <Trans i18nKey="hubTour:hubIntro">
        <div>
          <h3></h3>
          <p></p>
          <p></p>
        </div>
      </Trans>
    ),
    placement: "center",
    disableBeacon: true,
  },
  {
    target: '[data-tour="hub-source-example"]',
    content: (
      <Trans i18nKey="hubTour:selectSource">
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
    stage: "source",
  },
  {
    target: '[data-tour="hub-source-details"]',
    content: (
      <Trans i18nKey="hubTour:sourceDetails">
        <div>
          <h3></h3>
          <p></p>
        </div>
      </Trans>
    ),
    placement: "left",
    disableBeacon: true,
    disableBackButton: true,
    stage: "source",
  },
  {
    target: '[data-tour="hub-source-next-button"]',
    content: (
      <Trans i18nKey="hubTour:sourceNext">
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
    stage: "source",
  },
  {
    target: '[data-tour="hub-search"]',
    content: (
      <Trans i18nKey="hubTour:search">
        <div>
          <h3></h3>
          <p></p>
          <p>
            <strong></strong>
          </p>
          <p style={tipStyle}></p>
        </div>
      </Trans>
    ),
    placement: "bottom",
    disableBeacon: true,
    spotlightClicks: true,
    hideFooter: true,
    isInteractive: true,
    disableBackButton: true,
    stage: "grid",
  },
  {
    target: '[data-tour="hub-iris-card"]',
    content: (
      <Trans i18nKey="hubTour:selectDataset">
        <div>
          <h3></h3>
          <p></p>
          <p>
            <strong></strong>
          </p>
        </div>
      </Trans>
    ),
    placement: "right",
    disableBeacon: true,
    spotlightClicks: true,
    hideFooter: true,
    isInteractive: true,
    disableBackButton: true,
    stage: "grid",
  },
  {
    target: '[data-tour="hub-dataset-action"]',
    content: (
      <Trans i18nKey="hubTour:download">
        <div>
          <h3></h3>
          <p></p>
          <p>
            <strong></strong>
          </p>
        </div>
      </Trans>
    ),
    placement: "left",
    disableBeacon: true,
    spotlightClicks: true,
    hideFooter: true,
    isInteractive: true,
    disableBackButton: true,
    stage: "grid",
  },
  {
    target: '[data-tour="hub-datafiles-list"]',
    content: (
      <Trans i18nKey="hubTour:datafilesList">
        <div>
          <h3></h3>
          <p></p>
          <p></p>
        </div>
      </Trans>
    ),
    placement: "right",
    disableBeacon: true,
    disableBackButton: true,
    stage: "grid",
  },
  {
    target: '[data-tour="hub-dataset-add"]',
    content: (
      <Trans i18nKey="hubTour:addToDashAI">
        <div>
          <h3></h3>
          <p></p>
          <p>
            <strong></strong>
          </p>
          <p style={tipStyle}></p>
        </div>
      </Trans>
    ),
    placement: "left",
    disableBeacon: true,
    spotlightClicks: true,
    hideFooter: true,
    isInteractive: true,
    disableBackButton: true,
    stage: "grid",
  },
];

export const hubTourConfig = {
  continuous: true,
  showProgress: true,
  showSkipButton: true,
  showBackButton: true,
  disableOverlayClose: true,
  disableCloseOnEsc: false,
};
