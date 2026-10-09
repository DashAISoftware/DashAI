import { Trans } from "react-i18next";

export const notebookTourSteps = [
  {
    target: "body",
    content: (
      <Trans i18nKey="notebookTour:notebookIntro">
        <div>
          <h3></h3>
          <p></p>
        </div>
      </Trans>
    ),
    placement: "center",
    disableBeacon: true,
  },
  {
    target: '[data-tour="dataset-preview-section"]',
    content: (
      <Trans i18nKey="notebookTour:datasetPreview">
        <div>
          <h3></h3>
          <p></p>
          <p></p>
        </div>
      </Trans>
    ),
    placement: "bottom",
    disableBeacon: true,
  },
  {
    target: ".right-bar-container",
    content: (
      <Trans i18nKey="notebookTour:explorersPanel">
        <div>
          <h3></h3>
          <p></p>
          <p>
            <strong></strong>
          </p>
          <p>
            <strong></strong>
          </p>
          <p></p>
        </div>
      </Trans>
    ),
    placement: "left",
    disableBeacon: true,
  },
  {
    target: '[data-tour="histogram-explorer"]',
    content: (
      <Trans i18nKey="notebookTour:histogramExplorer">
        <div>
          <h3></h3>
          <p></p>
          <p></p>
        </div>
      </Trans>
    ),
    placement: "left",
    disableBeacon: true,
    spotlightClicks: true,
    hideFooter: true,
    isInteractive: true,
  },
  {
    target: '[data-tour="column-selector"]',
    content: (
      <Trans i18nKey="notebookTour:selectColumns">
        <div>
          <h3></h3>
          <p></p>
          <p>
            <strong></strong>
          </p>
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
    disableScrolling: true,
    disableBackButton: true,
    isInteractive: true,
    disableOverlay: true,
    maxWidth: "320px",
  },
  {
    target: '[data-tour="explorer-parameters"]',
    content: (
      <Trans i18nKey="notebookTour:configureParametersAndCreate">
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
    spotlightClicks: true,
    disableOverlay: true,
    isInteractive: true,
    disableScrolling: true,
    disableBackButton: true,
    maxWidth: "320px",
  },
  {
    target: ".explorer-box",
    content: (
      <Trans i18nKey="notebookTour:explorerCreated">
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
    placement: "top",
    disableBeacon: true,
    disableBackButton: true,
  },
  {
    target: '[data-tour="converters-tab"]',
    content: (
      <Trans i18nKey="notebookTour:convertersTab">
        <div>
          <h3></h3>
          <p></p>
          <p></p>
        </div>
      </Trans>
    ),
    placement: "left",
    disableBeacon: true,
    spotlightClicks: true,
    hideFooter: true,
    isInteractive: true,
  },
  {
    target: '[data-tour="label-encoder-converter"]',
    content: (
      <Trans i18nKey="notebookTour:labelEncoderConverter">
        <div>
          <h3></h3>
          <p></p>
          <p></p>
          <p></p>
        </div>
      </Trans>
    ),
    placement: "left",
    disableBeacon: true,
    spotlightClicks: true,
    hideFooter: true,
    isInteractive: true,
    disableBackButton: true,
  },
  {
    target: '[data-tour="column-selector-converter-container"]',
    content: (
      <Trans i18nKey="notebookTour:selectColumnsEncode">
        <div>
          <h3></h3>
          <p></p>
          <p></p>
          <ul>
            <li>
              <strong></strong>
            </li>
            <li>
              <strong></strong>
            </li>
          </ul>
          <p>
            <strong></strong>
          </p>
        </div>
      </Trans>
    ),
    placement: "right",
    disableBeacon: true,
    spotlightClicks: true,
    disableOverlay: true,
    hideFooter: true,
    disableScrolling: true,
    isInteractive: true,
    disableBackButton: true,
    maxWidth: "320px",
  },
  {
    target: ".converter-box",
    content: (
      <Trans i18nKey="notebookTour:converterApplied">
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
  },
  {
    target: ".save-dataset-button",
    content: (
      <Trans i18nKey="notebookTour:saveProcessedDataset">
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
    disableBeacon: true,
    spotlightClicks: true,
    hideFooter: true,
    isInteractive: true,
    disableBackButton: true,
  },
  {
    target: '[data-tour="save-dataset-modal-notebook"]',
    content: (
      <Trans i18nKey="notebookTour:finalStep">
        <div>
          <h3></h3>
          <p></p>
          <p></p>
          <hr style={{ margin: "15px 0", borderTop: "1px solid #ddd" }} />
          <h4></h4>
          <p></p>
          <ul style={{ marginBottom: "15px" }}>
            <li></li>
            <li></li>
            <li></li>
          </ul>
          <p
            style={{
              backgroundColor: "rgba(76, 175, 80, 0.12)",
              color: "inherit",
              padding: "8px",
              borderRadius: "4px",
              marginTop: "10px",
              borderLeft: "3px solid #43A047",
            }}
          >
            <strong></strong>
          </p>
        </div>
      </Trans>
    ),
    placement: "right",
    disableBeacon: true,
    spotlightClicks: true,
    disableScrolling: true,
    disableOverlayClose: true,
    showSkipButton: false,
    hideBackButton: false,
    disableOverlay: true,
    isInteractive: true,
    disableBackButton: true,
    styles: {
      options: {
        zIndex: 2000,
      },
      buttonNext: {
        backgroundColor: "#1976d2",
      },
      buttonBack: {
        color: "#1976d2",
      },
    },
    locale: {
      last: "Finish Tour",
      next: "Finish Tour",
    },
  },
];

export const notebookTourConfig = {
  continuous: true,
  showProgress: true,
  showSkipButton: true,
  showBackButton: true,
  disableOverlayClose: true,
  disableCloseOnEsc: false,
};
