import React, { useState, useEffect } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import {
  Modal,
  Card,
  CardHeader,
  CardActions,
  Container,
  Box,
} from "@mui/material";
import PropTypes from "prop-types";
import Upload from "../components/Upload";
import DatasetsTable from "../components/DatasetsTable";
import { getDefaultValues } from "../utils/values";
import ParameterForm from "../components/ParameterForm";
import * as S from "../styles/components/DatasetConfigStyles";
import { StyledButton, ErrorMessageDiv } from "../styles/globalComponents";
import { getSchema as getSchemaRequest } from "../api/oldEndpoints";
import { getDatasets as getDatasetsRequest } from "../api/datasets";
import { useSnackbar } from "notistack";

function SplitsParams({
  paramsSchema,
  handleSubmit,
  showSplitConfig,
  showMoreOptions,
  setShowMoreOptions,
  showSplitsError,
}) {
  /*
    If the JSON schema of dataloader have split configuration
    this section is showed. This component shows the parameters
    in a div section that can be hidden because it's depends if
    the user have the splits defined before or want to do it now,
    so a parameter control if this section is showed or not.

    Also, this section have an option of 'more options' that is
    showed only if the JSON schema have it. This is for advanced
    settings like set a seed, or shuffle the data.
  */
  let hideSection = showSplitConfig;
  if (showSplitConfig === "True") {
    hideSection = true;
  }
  if (showSplitConfig === "False") {
    hideSection = false;
  }
  return (
    <div>
      <S.HiddenSection style={{ maxHeight: !hideSection ? "500px" : "0px" }}>
        <hr />
        <p>Splits Configuration</p>
        {showSplitsError ? (
          <ErrorMessageDiv>The size of splits must sum to 1.</ErrorMessageDiv>
        ) : null}
        <ParameterForm
          type="splits"
          parameterSchema={paramsSchema}
          onFormSubmit={handleSubmit}
          showModal={false}
          onClose={() => {}}
          defaultValues={{ payload: getDefaultValues(paramsSchema) }}
        />
        {paramsSchema.more_options !== undefined ? (
          <StyledButton onClick={() => setShowMoreOptions(true)}>
            More Options
          </StyledButton>
        ) : null}
      </S.HiddenSection>
      {showMoreOptions ? (
        <ParameterForm
          type="Advanced"
          parameterSchema={paramsSchema.more_options}
          onFormSubmit={handleSubmit}
          showModal={showMoreOptions}
          onClose={() => setShowMoreOptions(false)}
          defaultValues={{
            payload: getDefaultValues(paramsSchema.more_options),
          }}
        />
      ) : null}
    </div>
  );
}

function ParamsModal({
  dataloader,
  paramsSchema,
  handleSubmit,
  showModal,
  setShowModal,
  showSplitConfig,
  setSplitConfig,
  showMoreOptions,
  setShowMoreOptions,
  setShowNameModal,
  showSplitsError,
  setShowUploadModal,
}) {
  /*
    To show the dataloader's parameters to be able to upload the data,
    is displayed a modal with ParameterForm, but inside this modal
    it is the splits div there, passed like a extra section.
   */
  const noClose = true;
  const handleBack = () => {
    setShowModal(false);
    setShowNameModal(true);
  };
  const handleClose = () => {
    setShowModal(false);
    setShowUploadModal(true);
  };
  return (
    <ParameterForm
      type={dataloader}
      parameterSchema={paramsSchema}
      onFormSubmit={handleSubmit}
      showModal={showModal}
      onClose={handleClose}
      defaultValues={{ payload: getDefaultValues(paramsSchema) }}
      extraOptions={
        <div style={{ marginBottom: "15px" }}>
          {paramsSchema.splits !== undefined ? (
            <SplitsParams
              paramsSchema={paramsSchema.splits}
              handleSubmit={handleSubmit} // TODO: build json to submit
              showSplitConfig={showSplitConfig}
              setSplitConfig={setSplitConfig}
              showMoreOptions={showMoreOptions}
              setShowMoreOptions={setShowMoreOptions}
              showSplitsError={showSplitsError}
            />
          ) : null}
        </div>
      }
      backdrop="static"
      noClose={noClose}
      onBack={handleBack}
      getValues={
        paramsSchema.properties.splits_in_folders !== undefined
          ? ["splits_in_folders", setSplitConfig]
          : null
      }
    />
  );
}

function Data() {
  // dataset state
  const EMPTY = 0;
  const [datasetState, setDatasetState] = useState(
    JSON.parse(localStorage.getItem("datasetState")) || EMPTY
  );
  useEffect(
    () => localStorage.setItem("datasetState", JSON.stringify(datasetState)),
    [datasetState]
  );
  const location = useLocation();
  const taskName = location.state?.taskName; // the task selected by user
  const dataloader = location.state?.dataloader; // the dataloader selected by user
  // const schemaRoute = `dataloader/${dataloader && dataloader.toLowerCase()}`; // name of the JSON schema for dataloader
  //
  const [showParams, setShowParams] = useState(location.state !== null);
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [paramsSchema, setParamsSchema] = useState();
  const [submitForm, setSubmitForm] = useState({
    task_name: taskName,
    dataloader,
  });
  //
  const [showSplitsError, setSplitsError] = useState(false);
  const [showSplitConfig, setSplitConfig] = useState(false);
  const [showMoreOptions, setShowMoreOptions] = useState(false);
  //
  const [datasets, setDatasets] = useState([]);
  const { enqueueSnackbar } = useSnackbar();
  useEffect(() => {
    setDatasetState(EMPTY);
    async function getSchema() {
      try {
        const schema = await getSchemaRequest(
          "dataloader",
          `${dataloader && dataloader.toLowerCase()}`
        );
        setParamsSchema(schema);
      } catch (error) {
        console.error(error);
      }
    }
    getSchema();
  }, []);

  useEffect(() => {
    async function getDatasets() {
      try {
        const datasets = await getDatasetsRequest();
        setDatasets(datasets);
      } catch (error) {
        console.error(error);
        enqueueSnackbar("Error while trying to obtain the datasets table.", {
          variant: "error",
          anchorOrigin: {
            vertical: "top",
            horizontal: "right",
          },
        });
      }
    }
    getDatasets();
  }, []);

  const handleSubmitParams = (modelName, values) => {
    /*
      How the parameters are in different sections,
      we need to join all the parameters in a single JSON
      to send to the endpoint. For that depending on the
      parameters model defined in backend (pydantic model)
      here is building that JSON of parameters.
    */
    const auxForm = submitForm;
    let sum = 0;
    const appendItemsToJSON = (object, items) => {
      for (let i = 0; i < Object.keys(items).length; i += 1) {
        const key = Object.keys(items)[i];
        const value = items[key];
        auxForm[object][key] = value;
      }
    };
    if (auxForm.splits === undefined) {
      // If user leaves the default values in split settings
      auxForm.splits = getDefaultValues(paramsSchema.splits);
      const moreOptions = getDefaultValues(paramsSchema.splits.more_options);
      appendItemsToJSON("splits", moreOptions);
    }
    switch (modelName) {
      case "splits": // Add the splits parameters
        sum = values.train_size + values.test_size + values.val_size;
        if (sum >= 0.999 && sum <= 1) {
          setSplitsError(false);
          appendItemsToJSON("splits", values);
          setSubmitForm(auxForm);
        } else {
          setSplitsError(true);
        }
        break;
      case "Advanced": // Add the more options parameters
        appendItemsToJSON("splits", values);
        setSubmitForm(auxForm);
        break;
      default: // Add the rest of parameters of principal modal
        auxForm.dataloader_params = values;
        if (values.class_column !== undefined) {
          auxForm.class_column = values.class_column;
          delete auxForm.dataloader_params.class_column;
        }
        if (values.splits_in_folders !== undefined) {
          auxForm.splits_in_folders = values.splits_in_folders;
          delete auxForm.dataloader_params.splits_in_folders;
        }
        setSubmitForm(auxForm);
    }
  };
  const navigate = useNavigate();
  const handleBackToHome = () => {
    navigate("/app", { state: { task: taskName } });
  };
  const handleNewDataset = () => {
    navigate("/app", { state: { newDataset: true } });
  };
  return (
    <Container>
      {showParams && paramsSchema ? (
        <ParamsModal
          dataloader={dataloader}
          paramsSchema={paramsSchema}
          handleSubmit={handleSubmitParams}
          showModal={showParams}
          setShowModal={setShowParams}
          showSplitConfig={showSplitConfig}
          setSplitConfig={setSplitConfig}
          showMoreOptions={showMoreOptions}
          setShowMoreOptions={setShowMoreOptions}
          setShowNameModal={handleBackToHome}
          showSplitsError={showSplitsError}
          setShowUploadModal={setShowUploadModal}
        />
      ) : null}
      <Modal
        open={showUploadModal}
        onClose={() => {
          showUploadModal(false);
        }}
        style={{
          position: "absolute",
          maxWidth: "60vw",
          minHeight: "40vh",
          left: "20%",
          top: "5%",
        }}
        aria-labelledby="modal-modal-title"
        aria-describedby="modal-modal-description"
      >
        <div>
          <Card
            variant="outlined"
            style={{ padding: "10px", backgroundColor: "#282a30" }}
          >
            <CardHeader
              avatar={
                <button
                  type="button"
                  className="bg-transparent"
                  onClick={() => {
                    setShowParams(true);
                    setShowUploadModal(false);
                  }}
                  style={{ float: "left", border: "none", marginLeft: "10px" }}
                >
                  <img alt="" src="/images/back.svg" width="30" height="30" />
                </button>
              }
            />
            <Box
              sx={{
                display: "flex",
                textAlign: "center",
                justifyContent: "center",
              }}
            >
              <Upload
                datasetState={datasetState}
                setDatasetState={setDatasetState}
                paramsData={submitForm}
                taskName={taskName}
              />
            </Box>
            <CardActions>
              <StyledButton
                style={{ marginLeft: "820px" }}
                onClick={() => setShowUploadModal()}
              >
                OK
              </StyledButton>
            </CardActions>
          </Card>
        </div>
      </Modal>
      <DatasetsTable
        initialRows={datasets}
        handleNewDataset={handleNewDataset}
      />
    </Container>
  );
}
SplitsParams.propTypes = {
  paramsSchema: PropTypes.objectOf(
    PropTypes.oneOfType([PropTypes.string, PropTypes.bool, PropTypes.object])
  ).isRequired,
  handleSubmit: PropTypes.func.isRequired,
  showSplitConfig: PropTypes.bool.isRequired,
  showMoreOptions: PropTypes.bool.isRequired,
  setShowMoreOptions: PropTypes.func.isRequired,
  showSplitsError: PropTypes.bool.isRequired,
};
ParamsModal.propTypes = {
  dataloader: PropTypes.string.isRequired,
  paramsSchema: PropTypes.objectOf(
    PropTypes.oneOfType([PropTypes.string, PropTypes.bool, PropTypes.object])
  ).isRequired,
  handleSubmit: PropTypes.func.isRequired,
  showModal: PropTypes.bool.isRequired,
  setShowModal: PropTypes.func.isRequired,
  showSplitConfig: PropTypes.bool.isRequired,
  setSplitConfig: PropTypes.func.isRequired,
  showMoreOptions: PropTypes.bool.isRequired,
  setShowMoreOptions: PropTypes.func.isRequired,
  setShowNameModal: PropTypes.func.isRequired,
  showSplitsError: PropTypes.bool.isRequired,
  setShowUploadModal: PropTypes.func.isRequired,
};
export default Data;
