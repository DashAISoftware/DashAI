import { Trans } from "react-i18next";

export const datasetsTourSteps = [
  {
    target: "body",
    content: (
      <Trans i18nKey="datasetsTour:datasetModule">
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
    target: '[data-tour="dataset-option"]',
    content: (
      <Trans i18nKey="datasetsTour:uploadDataset">
        <div>
          <h3></h3>
          <p></p>
          <p></p>
        </div>
      </Trans>
    ),
    placement: "bottom",
  },
  {
    target: '[data-tour="notebook-option"]',
    content: (
      <Trans i18nKey="datasetsTour:createNotebook">
        <div>
          <h3></h3>
          <p></p>
          <p></p>
        </div>
      </Trans>
    ),
    placement: "bottom",
  },
  {
    target: "body",
    content: (
      <Trans i18nKey="datasetsTour:downloadSample">
        <div>
          <h3></h3>
          <p></p>
          <p>
            <a
              href="/samples/personality_dataset.csv"
              download="personality_dataset.csv"
              style={{
                display: "inline-block",
                backgroundColor: "#2C7AFF",
                color: "#FEFEFF",
                padding: "10px 20px",
                textDecoration: "none",
                borderRadius: "4px",
                fontWeight: "bold",
                marginTop: "10px",
              }}
              onMouseOver={(e) => (e.target.style.backgroundColor = "#A7C7FF")}
              onMouseOut={(e) => (e.target.style.backgroundColor = "#2C7AFF")}
            ></a>
          </p>
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
          <p style={{ marginTop: "10px" }}></p>
        </div>
      </Trans>
    ),
    placement: "center",
    disableBeacon: true,
    spotlightClicks: true,
    hideFooter: false,
  },
  {
    target: '[data-tour="dataset-option"]',
    content: (
      <Trans i18nKey="datasetsTour:nowUpload">
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
    disableOverlayClose: true,
    isInteractive: true,
  },
  {
    target: '[data-tour="csv-dataloader-option"]',
    content: (
      <Trans i18nKey="datasetsTour:selectCsv">
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
    placement: "right",
    disableBeacon: true,
    spotlightClicks: true,
    disableBackButton: true,
    isInteractive: true,
  },
  {
    target: '[data-tour="dataloader-step-next-button"]',
    content: (
      <Trans i18nKey="datasetsTour:continueUpload">
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
  },

  {
    target: '[data-tour="upload-area"]',
    content: (
      <Trans i18nKey="datasetsTour:uploadFile">
        <div>
          <h3></h3>
          <p></p>
          <ul>
            <li>
              <strong></strong>
            </li>
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
          ></p>
        </div>
      </Trans>
    ),
    placement: "left",
    disableBeacon: true,
    spotlightClicks: true,
    disableBackButton: true,
    maxWidth: "320px",
  },
  {
    target: '[data-tour="dataloader-config"]',
    content: (
      <Trans i18nKey="datasetsTour:dataLoaderConfig">
        <div>
          <h3></h3>
          <p></p>
          <ul>
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
    placement: "left",
    disableBeacon: true,
    spotlightClicks: true,
  },
  {
    target: '[data-tour="dataset-step-upload-button"]',
    content: (
      <Trans i18nKey="datasetsTour:completeUpload">
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
  },
];

export const datasetsTourConfig = {
  continuous: true,
  showProgress: true,
  showSkipButton: true,
  showBackButton: true,
  disableOverlayClose: true,
  disableCloseOnEsc: false,
};
