import React, { useState, useRef } from 'react';
import PropTypes from 'prop-types';
import { useNavigate } from 'react-router-dom';
import { P } from '../styles/globalComponents';
import {
  FormFileUpload,
  LabelFileUpload,
  UploadButton,
  DragFile,
} from '../styles/components/UploadStyles';

function Upload({ setModels, setTaskName, setShowUpload }) {
  Upload.propTypes = {
    setModels: PropTypes.func.isRequired,
    setTaskName: PropTypes.func.isRequired,
    setShowUpload: PropTypes.func.isRequired,
  };
  const navigate = useNavigate();
  const [dragActive, setDragActive] = useState(false);
  const inputRef = useRef(null);
  const uploadFile = async (file) => {
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
      setShowUpload(false);
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
  return (
    <div>
      <P>Upload your dataset</P>
      <FormFileUpload onDragEnter={handleDrag}>
        <LabelFileUpload htmlFor="input-upload-dataset" className={dragActive ? 'drag-active' : ''}>
          <input ref={inputRef} id="input-upload-dataset" style={{ display: 'none' }} type="file" onChange={handleSelect} />
          <p>Drag and drop your file here or</p>
          <UploadButton type="button" onClick={handleButtonClick}>Upload a file</UploadButton>
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
    </div>
  );
}

export default Upload;
