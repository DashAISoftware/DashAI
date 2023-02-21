import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import PropTypes from 'prop-types';
import Upload from '../components/Upload';
import { getDefaultValues } from '../utils/values';
import ParameterForm from '../components/ParameterForm';
import * as S from '../styles/components/DatasetConfigStyles';
import {
  CustomContainer,
  StyledButton,
  SubTitle,
  ErrorMessageDiv,
} from '../styles/globalComponents';

function SplitsParams({
  paramsSchema,
  handleSubmit,
  showSplitConfig,
  showMoreOptions,
  setShowMoreOptions,
  showSplitsError,
}) {
  let hideSection = showSplitConfig;
  if (showSplitConfig === 'True') { hideSection = true; }
  if (showSplitConfig === 'False') { hideSection = false; }
  return (
    <div>
      <S.HiddenSection style={{ maxHeight: !hideSection ? '500px' : '0px' }}>
        <hr />
        <p>Splits Configuration</p>
        { showSplitsError ? (
          <ErrorMessageDiv>The size of splits must sum to 1.</ErrorMessageDiv>
        ) : null }
        <ParameterForm
          type="splits"
          parameterSchema={paramsSchema}
          handleFormSubmit={handleSubmit}
          showModal={false}
          handleModalClose={() => {}}
          defaultValues={{ payload: getDefaultValues(paramsSchema) }}
        />
        { paramsSchema.more_options !== undefined ? (
          <StyledButton onClick={() => setShowMoreOptions(true)}>More Options</StyledButton>
        ) : null }
      </S.HiddenSection>
      { showMoreOptions ? (
        <ParameterForm
          type="Advanced"
          parameterSchema={paramsSchema.more_options}
          handleFormSubmit={handleSubmit}
          showModal={showMoreOptions}
          handleModalClose={() => setShowMoreOptions(false)}
          defaultValues={{ payload: getDefaultValues(paramsSchema.more_options) }}
        />
      ) : null }
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
      extraOptions={(
        <div style={{ marginBottom: '15px' }}>
          { paramsSchema.splits !== undefined ? (
            <SplitsParams
              paramsSchema={paramsSchema.splits}
              handleSubmit={handleSubmit} // TODO: build json to submit
              showSplitConfig={showSplitConfig}
              setSplitConfig={setSplitConfig}
              showMoreOptions={showMoreOptions}
              setShowMoreOptions={setShowMoreOptions}
              showSplitsError={showSplitsError}
            />
          ) : null }
        </div>
        )}
      backdrop="static"
      noClose={noClose}
      handleBack={handleBack}
      getValues={(paramsSchema.properties.splits_in_folders !== undefined)
        ? ['splits_in_folders', setSplitConfig] : null}
    />
  );
}

function Data() {
  // dataset state
  const EMPTY = 0;
  const [datasetState, setDatasetState] = useState(JSON.parse(localStorage.getItem('datasetState')) || EMPTY);
  useEffect(() => localStorage.setItem('datasetState', JSON.stringify(datasetState)), [datasetState]);
  //
  // const [taskName, setTaskName] = useState(JSON.parse(localStorage.getItem('taskName')) || '');
  // useEffect(() => localStorage.setItem('taskName', JSON.stringify(taskName)), [taskName]);
  const location = useLocation();
  const taskName = location.state?.taskName;
  const dataloader = location.state?.dataloader;
  const schemaRoute = `dataloader/${dataloader.toLowerCase()}`;
  //
  const [showParams, setShowParams] = useState(false);
  const [showNameModal, setShowNameModal] = useState(true);
  const [paramsSchema, setParamsSchema] = useState();
  const [datasetName, setDatasetName] = useState('');
  const [submitForm, setSubmitForm] = useState({ task_name: taskName, data_loader: dataloader });
  //
  const [showSplitsError, setSplitsError] = useState(false);
  const [showSplitConfig, setSplitConfig] = useState(false);
  const [showMoreOptions, setShowMoreOptions] = useState(false);
  //
  useEffect(() => {
    setDatasetState(EMPTY);
    async function fetchParams() {
      const response = await fetch(`${process.env.REACT_APP_SELECT_SCHEMA_ENDPOINT + schemaRoute}`);
      if (!response.ok) {
        throw new Error('Data could not be obtained.');
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
      auxForm.splits = getDefaultValues(paramsSchema.splits);
      const moreOptions = getDefaultValues(paramsSchema.splits.more_options);
      appendItemsToJSON('splits', moreOptions);
    }
    switch (modelName) {
      case 'splits':
        sum = values.train_size + values.test_size + values.val_size;
        if (sum !== 1) {
          setSplitsError(true);
        } else {
          setSplitsError(false);
          appendItemsToJSON('splits', values);
          setSubmitForm(auxForm);
        }
        break;
      case 'Advanced':
        appendItemsToJSON('splits', values);
        setSubmitForm(auxForm);
        break;
      default:
        auxForm.dataloader_params = values;
        if (values.class_column !== undefined) {
          auxForm.class_column = values.class_column;
          delete auxForm.dataloader_params.class_column;
        }
        if (values.splits_in_folders !== undefined) {
          auxForm.folder_splits = values.splits_in_folders;
          delete auxForm.dataloader_params.splits_in_folders;
        }
        setSubmitForm(auxForm);
    }
  };
  const navigate = useNavigate();
  const handleBackToHome = () => {
    navigate('/', { state: { task: taskName } });
  };
  return (
    <div>
      <S.Modal backdrop="static" show={showNameModal} onHide={() => setShowNameModal(false)}>
        <S.Modal.Header>
          <button
            type="button"
            className="bg-transparent"
            onClick={handleBackToHome}
            style={{ float: 'left', border: 'none', marginLeft: '10px' }}
          >
            <img
              alt=""
              src="images/back.svg"
              width="30"
              height="30"
            />
          </button>
          <SubTitle style={{ marginRight: '50px' }}>Name your dataset</SubTitle>
        </S.Modal.Header>
        <S.Modal.Body style={{ textAlign: 'center' }}>
          <S.TextInput
            type="text"
            value={datasetName}
            placeholder="Write a name ..."
            onChange={(e) => setDatasetName(e.target.value)}
            style={{ background: 'transparent', padding: '5px 10px' }}
          />
          <StyledButton onClick={handleSetName} style={{ marginLeft: '10px' }}>Ok</StyledButton>
        </S.Modal.Body>
        <S.Modal.Footer />
      </S.Modal>
      { showParams ? (
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
      ) : null }
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
    PropTypes.oneOfType([
      PropTypes.string,
      PropTypes.bool,
      PropTypes.object,
    ]),
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
    PropTypes.oneOfType([
      PropTypes.string,
      PropTypes.bool,
      PropTypes.object,
    ]),
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
