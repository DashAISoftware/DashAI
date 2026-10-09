import { Trans } from "react-i18next";

export const modelsTourSteps = [
  {
    target: "body",
    content: (
      <Trans i18nKey="modelsTour:modelsModule">
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
    target: '[data-tour="models-left-panel"]',
    content: (
      <Trans i18nKey="modelsTour:sessionsPanel">
        <div>
          <h3></h3>
          <p></p>
          <p>
            <strong></strong>
          </p>
          <p></p>
        </div>
      </Trans>
    ),
    placement: "right",
    disableBeacon: true,
  },
  {
    target: '[data-tour="models-center-panel"]',
    content: (
      <Trans i18nKey="modelsTour:mainWorkspace">
        <div>
          <h3></h3>
          <p></p>
          <p></p>
        </div>
      </Trans>
    ),
    placement: "right",
    disableBeacon: true,
    maxWidth: "320px",
  },
  {
    target: '[data-tour="models-right-panel"]',
    content: (
      <Trans i18nKey="modelsTour:modelsPanel">
        <div>
          <h3></h3>
          <p></p>
          <p></p>
        </div>
      </Trans>
    ),
    placement: "left",
    disableBeacon: true,
  },
  {
    target: '[data-tour="task-selection"]',
    content: (
      <Trans i18nKey="modelsTour:selectTask">
        <div>
          <h3></h3>
          <p></p>
          <p></p>
          <ul style={{ marginLeft: "20px", lineHeight: "1.6" }}>
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
    isInteractive: true,
  },
  {
    target: '[data-tour="models-dataset-selection"]',
    content: (
      <Trans i18nKey="modelsTour:selectDataset">
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
    disableBackButton: true,
    maxWidth: "320px",
  },
  {
    target: '[data-tour="models-validation-alert"]',
    content: (
      <Trans i18nKey="modelsTour:columnValidation">
        <div>
          <h3></h3>
          <p></p>
          <p>
            <strong style={{ color: "#43A047" }}></strong>
          </p>
          <p>
            <strong style={{ color: "#e53935" }}></strong>
          </p>
          <p></p>
        </div>
      </Trans>
    ),
    placement: "right",
    disableBeacon: true,
    disableBackButton: true,
  },
  {
    target: '[data-tour="dataset-input-columns-autocomplete"]',
    content: (
      <Trans i18nKey="modelsTour:inputColumns">
        <div>
          <h3></h3>
          <p>
            <strong></strong>
          </p>
          <p></p>
          <ul style={{ marginLeft: "20px", lineHeight: "1.6" }}>
            <li></li>
            <li></li>
          </ul>
          <p></p>
        </div>
      </Trans>
    ),
    placement: "right",
    disableBeacon: true,
    spotlightClicks: true,
    disableOverlay: true,
    maxWidth: "320px",
  },
  {
    target: '[data-tour="dataset-output-columns-autocomplete"]',
    content: (
      <Trans i18nKey="modelsTour:outputColumns">
        <div>
          <h3></h3>
          <p>
            <strong></strong>
          </p>
          <p></p>
          <ul style={{ marginLeft: "20px", lineHeight: "1.6" }}>
            <li></li>
            <li></li>
            <li></li>
          </ul>
          <p></p>
        </div>
      </Trans>
    ),
    placement: "right",
    disableBeacon: true,
    spotlightClicks: true,
    disableOverlay: true,
    maxWidth: "320px",
  },
  {
    target: '[data-tour="exp-dataset-splits"]',
    content: (
      <Trans i18nKey="modelsTour:datasetSplits">
        <div>
          <h3></h3>
          <p></p>
          <p>
            <strong></strong>
          </p>
          <p>
            <strong></strong>
          </p>
          <p>
            <strong></strong>
          </p>
          <p>
            <strong></strong>
            <strong></strong>
            <strong></strong>
          </p>
        </div>
      </Trans>
    ),
    placement: "left",
    disableBeacon: true,
    maxWidth: "320px",
  },
  {
    target: '[data-tour="models-next-button"]',
    content: (
      <Trans i18nKey="modelsTour:createSession">
        <div>
          <h3></h3>
          <p></p>
          <p>
            <strong></strong>
          </p>
          <p>
            <strong></strong>
          </p>
          <p
            style={{ marginTop: "10px", fontSize: "14px", color: "inherit" }}
          ></p>
        </div>
      </Trans>
    ),
    placement: "top",
    disableBeacon: true,
    spotlightClicks: true,
    isInteractive: true,
  },
];

export const modelsTourConfig = {
  continuous: true,
  showProgress: true,
  showBackButton: true,
  showSkipButton: true,
  disableOverlayClose: true,
  disableCloseOnEsc: false,
};
