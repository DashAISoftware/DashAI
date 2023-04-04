import React, { useState, useEffect } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import PropTypes from "prop-types";
import Upload from "../components/Upload";
import { getDefaultValues } from "../utils/values";
import ParameterForm from "../components/ParameterForm";
import * as S from "../styles/components/DatasetConfigStyles";
import {
  CustomContainer,
  StyledButton,
  SubTitle,
  ErrorMessageDiv,
} from "../styles/globalComponents";

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
          handleFormSubmit={handleSubmit}
          showModal={false}
          handleModalClose={() => {}}
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
          handleFormSubmit={handleSubmit}
          showModal={showMoreOptions}
          handleModalClose={() => setShowMoreOptions(false)}
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
  return (
    <ParameterForm
      type={dataloader}
      parameterSchema={paramsSchema}
      handleFormSubmit={handleSubmit}
      showModal={showModal}
      handleModalClose={() => setShowModal(false)}
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
      handleBack={handleBack}
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
  //
  // --- NOTE ---
  // Isn't used the JSON dataset with the task name in it anymore, now is taken from user input.
  // -----------
  // const [taskName, setTaskName] = useState(JSON.parse(localStorage.getItem('taskName')) || '');
  // useEffect(() => localStorage.setItem('taskName', JSON.stringify(taskName)), [taskName]);
  const location = useLocation();
  const taskName = location.state?.taskName; // the task selected by user
  const dataloader = location.state?.dataloader; // the dataloader selected by user
  const schemaRoute = `dataloader/${dataloader && dataloader.toLowerCase()}`; // name of the JSON schema for dataloader
  //
  const [showParams, setShowParams] = useState(false);
  const [showNameModal, setShowNameModal] = useState(location.state !== null);
  const [paramsSchema, setParamsSchema] = useState();
  const [datasetName, setDatasetName] = useState("");
  const [submitForm, setSubmitForm] = useState({
    task_name: taskName,
    dataloader,
  });
  //
  const [showSplitsError, setSplitsError] = useState(false);
  const [showSplitConfig, setSplitConfig] = useState(false);
  const [showMoreOptions, setShowMoreOptions] = useState(false);
  //
  useEffect(() => {
    setDatasetState(EMPTY);
    async function fetchParams() {
      const response = await fetch(
        `${process.env.REACT_APP_SELECT_SCHEMA_ENDPOINT + schemaRoute}`
      );
      if (!response.ok) {
        throw new Error("Data could not be obtained.");
      } else {
        const schema = await response.json();
        setParamsSchema(schema);
      }
    }
    fetchParams();
  }, []);
  const handleSetName = () => {
    // TODO: Request for check if the name already exists
    const auxForm = submitForm;
    auxForm.dataset_name = datasetName;
    setSubmitForm(auxForm);
    setShowNameModal(false);
    setShowParams(true);
  };
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
  return (
    <div>
      <S.Modal
        backdrop="static"
        show={showNameModal}
        onHide={() => setShowNameModal(false)}
      >
        <S.Modal.Header>
          <button
            type="button"
            className="bg-transparent"
            onClick={handleBackToHome}
            style={{ float: "left", border: "none", marginLeft: "10px" }}
          >
            <img alt="" src="/images/back.svg" width="30" height="30" />
          </button>
          <SubTitle style={{ marginRight: "50px" }}>Name your dataset</SubTitle>
        </S.Modal.Header>
        <S.Modal.Body style={{ textAlign: "center" }}>
          <S.TextInput
            type="text"
            value={datasetName}
            placeholder="Write a name ..."
            onChange={(e) => setDatasetName(e.target.value)}
            style={{ background: "transparent", padding: "5px 10px" }}
          />
          <StyledButton onClick={handleSetName} style={{ marginLeft: "10px" }}>
            Ok
          </StyledButton>
        </S.Modal.Body>
        <S.Modal.Footer />
      </S.Modal>
      {showParams && location.state ? (
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
          setShowNameModal={setShowNameModal}
          showSplitsError={showSplitsError}
        />
      ) : null}
      <CustomContainer>
        <Upload
          datasetState={datasetState}
          setDatasetState={setDatasetState}
          paramsData={JSON.stringify(submitForm)}
          taskName={taskName}
          // setTaskName={setTaskName}
        />
      </CustomContainer>
    </div>
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
};
export default Data;
