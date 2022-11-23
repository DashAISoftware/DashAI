import React, { useState, useRef } from 'react';
import PropTypes from 'prop-types';
// import { useNavigate } from 'react-router-dom';
import {
  P,
  Title,
  StyledButton,
  Loading,
} from '../styles/globalComponents';
import * as S from '../styles/components/UploadStyles';
import Error from './Error';

function Upload({
  setCompatibleModels,
  datasetState,
  setDatasetState,
  taskName,
  setTaskName,
  resetAppState,
  scrollToNextStep,
  error,
  setError,
}) {
  // const navigate = useNavigate();
  const [EMPTY, LOADING, LOADED] = [0, 1, 2];
  // const [datasetState, setDatasetState] = useState(datasetIsLoaded ? LOADED : EMPTY);
  // const [taskName, setTaskName] = useState('');
  const [dragActive, setDragActive] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const inputRef = useRef(null);
  const uploadFile = async (file) => {
    resetAppState();
    setDatasetState(LOADING);
    const formData = new FormData();
    formData.append('file', file);
    try {
      const fetchedModels = await fetch(
        `${process.env.REACT_APP_DATASET_UPLOAD_ENDPOINT}`,
        { method: 'POST', body: formData },
      );

      const models = await fetchedModels.json();
      const sessionId = 0;
      const fetchedTask = await fetch(`${process.env.REACT_APP_TASK_NAME_ENDPOINT + sessionId}`);
      const task = await fetchedTask.json();
      if (typeof models.message !== 'undefined') {
        // navigate('/error');
        setError(true);
        setErrorMessage(models.message);
      } else {
        setCompatibleModels(models.models);
        setTaskName(task);
        setDatasetState(LOADED);
      }
    } catch (e) {
      // navigate('/error');
      setError(true);
      setErrorMessage('Failed request to API');
    }
  };
  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };
  const handleSelect = (e) => {
    uploadFile(e.target.files[0]);
  };
  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      uploadFile(e.dataTransfer.files[0]);
    }
  };
  const handleButtonClick = () => {
    inputRef.current.click();
  };
  const stateText = (state) => {
    switch (state) {
      case (EMPTY): return ('Upload your dataset');
      case (LOADING): return ('Loading dataset');
      case (LOADED): return ('Uploaded dataset');
      default: return ('');
    }
  };
  const stateImg = (state) => {
    switch (state) {
      case (EMPTY):
        return (
          <div>
            <input ref={inputRef} id="input-upload-dataset" style={{ display: 'none' }} type="file" onChange={handleSelect} />
            <p>Drag and drop your file here or</p>
            <S.UploadButton type="button" onClick={handleButtonClick}>Upload a file</S.UploadButton>
          </div>
        );
      case (LOADING):
        return (
          <Loading
            alt=""
            src="images/loading.png"
            width="58"
            height="58"
          />
        );
      case (LOADED):
        return (
          <img
            alt=""
            src="images/loaded.png"
            width="58"
            height="58"
          />
        );
      default:
        return (<div />);
    }
  };
  if (error) {
    return (<Error message={errorMessage} reset={resetAppState} />);
  }
  return (
    <div>
      <Title>Load Dataset</Title>
      <br />
      <br />
      <P>
        {stateText(datasetState)}
      </P>
      <S.FormFileUpload onDragEnter={handleDrag}>
        <S.LabelFileUpload htmlFor="input-upload-dataset" className={dragActive ? 'drag-active' : ''}>
          { stateImg(datasetState) }
        </S.LabelFileUpload>
        { dragActive
          && (
            <S.DragFile
              onDragEnter={handleDrag}
              onDragLeave={handleDrag}
              onDragOver={handleDrag}
              onDrop={handleDrop}
            />
          )}
      </S.FormFileUpload>
      <br />
      { taskName !== ''
        && <P style={{ fontSize: '18px', lineHeight: '22.5px' }}>{`Task Type: ${taskName}`}</P>}
      <br />
      { datasetState === LOADED
      && (
      <div style={{ flexDirection: 'row' }}>
        <StyledButton type="button" style={{ marginRight: '10px' }} onClick={resetAppState}>Reset</StyledButton>
        <StyledButton type="button" onClick={scrollToNextStep}>Next</StyledButton>
      </div>
      )}
    </div>
  );
}
Upload.propTypes = {
  setCompatibleModels: PropTypes.func.isRequired,
  datasetState: PropTypes.number.isRequired,
  setDatasetState: PropTypes.func.isRequired,
  taskName: PropTypes.string.isRequired,
  setTaskName: PropTypes.func.isRequired,
  resetAppState: PropTypes.func.isRequired,
  scrollToNextStep: PropTypes.func.isRequired,
  error: PropTypes.bool.isRequired,
  setError: PropTypes.func.isRequired,
};
export default Upload;
