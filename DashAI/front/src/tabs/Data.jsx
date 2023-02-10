import React, { useState, useEffect } from 'react';
import PropTypes from 'prop-types';
import { useLocation } from 'react-router-dom';
import Upload from '../components/Upload';
import { getDefaultValues } from '../utils/values';
import ParameterForm from '../components/ParameterForm';
import * as S from '../styles/components/SchemaListStyles';
import { CustomContainer, StyledButton, SubTitle } from '../styles/globalComponents';

function ParamsModal({
  dataloader,
  paramsSchema,
  handleSubmit,
  showModal,
  setShowModal,
}) {
  return (
    <ParameterForm
      type={dataloader.toLowerCase()}
      parameterSchema={paramsSchema}
      handleFormSubmit={handleSubmit}
      defaultValues={getDefaultValues(paramsSchema)}
      showModal={showModal}
      handleModalClose={() => setShowModal(false)}
    />
  );
}
function SplitsModal({
  paramsSchema,
  handleSubmit,
  showModal,
  setShowModal,
}) {
  return (
    <ParameterForm
      type="splits"
      parameterSchema={paramsSchema}
      handleFormSubmit={handleSubmit}
      defaultValues={getDefaultValues(paramsSchema)}
      showModal={showModal}
      handleModalClose={() => setShowModal(false)}
    />
  );
}
function Data() {
  // dataset state
  const EMPTY = 0;
  // localStorage.removeItem('datasetState');
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
  const [showSplitParams, setShowSplitParams] = useState(false);
  const [paramsSchema, setParamsSchema] = useState();
  const [splitsSchema, setSplitsSchema] = useState();
  const [datasetName, setDatasetName] = useState('');
  const [submitForm, setSubmitForm] = useState({ task_name: taskName, data_loader: dataloader });
  // JSON.stringify to parse submitForm to str and send it in POST request
  useEffect(() => {
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
  useEffect(() => {
    async function fetchSplitParams() {
      const response = await fetch(`${process.env.REACT_APP_SELECT_SCHEMA_ENDPOINT}dataloader/splits`);
      if (!response.ok) {
        throw new Error('Data could not be obtained.');
      } else {
        const schema = await response.json();
        setSplitsSchema(schema);
      }
    }
    fetchSplitParams();
  }, []);
  const handleSetName = () => {
    const auxForm = submitForm;
    auxForm.dataset_name = datasetName;
    setSubmitForm(auxForm);
    setShowNameModal(false);
    setShowParams(true);
  };
  const handleSubmitParams = (modelName, values) => {
    const auxForm = submitForm;
    auxForm.dataloader_params = values;
    setSubmitForm(auxForm);
    if (values.splits) {
      setShowSplitParams(true);
    }
  };
  const handleSubmitSplits = (modelName, values) => {
    const auxForm = submitForm;
    auxForm.splits = values;
    setSubmitForm(auxForm);
  };
  return (
    <div>
      <S.Modal show={showNameModal} onHide={() => setShowNameModal(false)}>
        <S.Modal.Header>
          <SubTitle>Name your dataset</SubTitle>
        </S.Modal.Header>
        <S.Modal.Body style={{ textAlign: 'center' }}>
          <S.SearchBar
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
        />
      ) : null }
      { showSplitParams ? (
        <SplitsModal
          paramsSchema={splitsSchema}
          handleSubmit={handleSubmitSplits}
          showModal={showSplitParams}
          setShowModal={setShowSplitParams}
        />
      ) : null }
      <CustomContainer>
        <Upload
          datasetState={datasetState}
          setDatasetState={setDatasetState}
          taskName={taskName}
          // setTaskName={setTaskName}
        />
      </CustomContainer>
    </div>
  );
}
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
};
SplitsModal.propTypes = {
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
};
export default Data;
