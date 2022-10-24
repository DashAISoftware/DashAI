import React, { useState, useRef } from 'react';
import PropTypes from 'prop-types';
import { useNavigate } from 'react-router-dom';
import styled from 'styled-components';
import {
  P,
  Title,
  StyledButton,
} from '../styles/globalComponents';
import {
  FormFileUpload,
  LabelFileUpload,
  UploadButton,
  DragFile,
} from '../styles/components/UploadStyles';

const Uploading = styled.img`
  @keyframes spin {
    from {transform:rotate(0deg);}
    to {transform:rotate(360deg);}
  }
  animation: spin 3s linear infinite;
`;

function Upload({ setModels, scrollToNextStep }) {
  Upload.propTypes = {
    setModels: PropTypes.func.isRequired,
    scrollToNextStep: PropTypes.func.isRequired,
  };
  const navigate = useNavigate();
  // const { empty, loading, loaded } = [0, 1, 2];
  const [datasetState, setDatasetState] = useState(0);
  const [taskName, setTaskName] = useState('');
  const [dragActive, setDragActive] = useState(false);
  const inputRef = useRef(null);
  const uploadFile = async (file) => {
    setDatasetState(1);
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
      setTaskName(task);
      setDatasetState(2);
      if (typeof models.error !== 'undefined') {
        navigate('/error');
      } else {
        setModels(models.models);
      }
    } catch (error) {
      navigate('/error');
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
      case (0): return ('Upload your dataset');
      case (1): return ('Loading dataset');
      case (2): return ('Uploaded dataset');
      default: return ('');
    }
  };
  const stateImg = (state) => {
    switch (state) {
      case (0):
        return (
          <div>
            <input ref={inputRef} id="input-upload-dataset" style={{ display: 'none' }} type="file" onChange={handleSelect} />
            <p>Drag and drop your file here or</p>
            <UploadButton type="button" onClick={handleButtonClick}>Upload a file</UploadButton>
          </div>
        );
      case (1):
        return (
          <Uploading
            alt=""
            src="images/loading.png"
            width="58"
            height="58"
          />
        );
      case (2):
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
  return (
    <div>
      <Title>Load Dataset</Title>
      <br />
      <br />
      <P>
        {stateText(datasetState)}
      </P>
      <FormFileUpload onDragEnter={handleDrag}>
        <LabelFileUpload htmlFor="input-upload-dataset" className={dragActive ? 'drag-active' : ''}>
          { stateImg(datasetState) }
        </LabelFileUpload>
        { dragActive
          && (
            <DragFile
              onDragEnter={handleDrag}
              onDragLeave={handleDrag}
              onDragOver={handleDrag}
              onDrop={handleDrop}
            />
          )}
      </FormFileUpload>
      <br />
      { taskName !== ''
        && <P style={{ fontSize: '18px', lineHeight: '22.5px' }}>{`Task Type: ${taskName}`}</P>}
      <br />
      { datasetState === 2
      && <StyledButton type="button" onClick={scrollToNextStep}>Next</StyledButton>}
    </div>
  );
}

export default Upload;
