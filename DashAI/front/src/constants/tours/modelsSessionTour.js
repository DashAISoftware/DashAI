import { maxWidth } from "@mui/system";
import { Trans } from "react-i18next";

export const modelsSessionTourSteps = [
  {
    target: "body",
    content: (
      <Trans i18nKey="modelsSessionTour:sessionVisualization">
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
    target: '[data-tour="models-right-panel"]',
    content: (
      <Trans i18nKey="modelsSessionTour:availableModels">
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
    target: '[data-tour="first-model"]',
    content: (
      <Trans i18nKey="modelsSessionTour:addFirstModel">
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
    isInteractive: true,
  },
  {
    target: '[data-tour="model-config"]',
    content: (
      <Trans i18nKey="modelsSessionTour:modelConfig">
        <div>
          <h3></h3>
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
    disableScrolling: true,
    disableScrollParentFix: true,
    disableOverlay: true,
    spotlightClicks: true,
    isInteractive: true,
    maxWidth: "320px",
  },
  {
    target: '[data-tour="first-run-card"]',
    content: (
      <Trans i18nKey="modelsSessionTour:modelRunCard">
        <div>
          <h3></h3>
          <p></p>
          <ul style={{ marginLeft: "20px", lineHeight: "1.6" }}>
            <li>
              <strong></strong>
            </li>
            <li>
              <strong></strong>
            </li>
            <li>
              <strong></strong>
            </li>
            <li>
              <strong></strong>
            </li>
          </ul>
          <p></p>
        </div>
      </Trans>
    ),
    placement: "right",
    disableBeacon: true,
    disableScrolling: true,
    disableScrollParentFix: true,
  },
  {
    target: '[data-tour="train-button"]',
    content: (
      <Trans i18nKey="modelsSessionTour:trainModel">
        <div>
          <h3></h3>
          <p>
            <strong></strong>
          </p>
          <p></p>
          <p>
            <strong></strong>
          </p>
        </div>
      </Trans>
    ),
    placement: "top",
    disableBeacon: true,
    spotlightClicks: true,
    isInteractive: true,
    disableBackButton: true,
  },
  {
    target: '[data-tour="model-comparison-panel"]',
    content: (
      <Trans i18nKey="modelsSessionTour:modelComparison">
        <div>
          <h3></h3>
          <p></p>
          <ul style={{ marginLeft: "20px", lineHeight: "1.6" }}>
            <li>
              <strong></strong>
            </li>
            <li>
              <strong></strong>
            </li>
            <li>
              <strong></strong>
            </li>
          </ul>
          <p></p>
        </div>
      </Trans>
    ),
    placement: "right",
    disableBeacon: true,
    maxWidth: "420px",
  },
  {
    target: '[data-tour="model-comparison-panel"]',
    content: (
      <Trans i18nKey="modelsSessionTour:performanceVisualizations">
        <div>
          <h3></h3>
          <p></p>
          <p style={{ marginTop: "12px" }}>
            🎉 <strong></strong>
          </p>
        </div>
      </Trans>
    ),
    placement: "right",
    disableBeacon: true,
    disableScrolling: true,
    disableScrollParentFix: true,
    disableOverlay: true,
    spotlightClicks: true,
    maxWidth: "320px",
  },
];

export const modelsSessionTourConfig = {
  continuous: true,
  showProgress: true,
  showBackButton: true,
  showSkipButton: true,
  disableOverlayClose: true,
  disableCloseOnEsc: false,
  disableScrollParentFix: true,
  locale: {
    back: "Back",
    close: "Close",
    last: "Finish",
    next: "Next",
    skip: "Skip Tour",
  },
};
