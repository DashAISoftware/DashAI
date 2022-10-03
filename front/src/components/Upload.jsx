import React from 'react';
// import React, { useState } from 'react';
import Form from 'react-bootstrap/Form';
import PropTypes from 'prop-types';
import { useNavigate } from 'react-router-dom';

function Upload({ setModels, setTaskName }) {
  Upload.propTypes = {
    setModels: PropTypes.func.isRequired,
    setTaskName: PropTypes.func.isRequired,
  };
  const navigate = useNavigate();
  const handleFileSelect = async (event) => {
    const formData = new FormData();
    formData.append('file', event.target.files[0]);
    try {
      const fetchedModels = await fetch(
        'http://localhost:8000/dataset/upload/',
        { method: 'POST', body: formData },
      );
      const models = await fetchedModels.json();
      const sessionId = 0;
      const fetchedTask = await fetch(`http://localhost:8000/dataset/task_name/${sessionId}`);
      const task = await fetchedTask.json();
      setTaskName(task);
      if (typeof models.error !== 'undefined') {
        navigate('/error');
        // setModels(['none']);
      } else {
        setModels(models.models);
      }
    } catch (error) {
      navigate('/error');
    }
  };

  return (
    <Form>
      <Form.Group controlId="formFileLg" className="mb-3">
        <Form.Label>Upload your dataset.</Form.Label>
        <Form.Control type="file" onChange={handleFileSelect} />
      </Form.Group>
    </Form>
  );
}

export default Upload;
