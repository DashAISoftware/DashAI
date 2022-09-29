import React from 'react';
// import React, { useState } from 'react';
import Form from 'react-bootstrap/Form';
import PropTypes from 'prop-types';

function Upload({ setModels, setTaskName }) {
  Upload.propTypes = {
    setModels: PropTypes.func.isRequired,
    setTaskName: PropTypes.func.isRequired,
  };
  // const [file, setFile] = useState(null);
  // const handleSubmit = async (e) => {
  //   e.preventDefault();
  //
  //   const formData = new FormData();
  //   formData.append('file', file);
  //   const fetchedModels = await fetch('http://localhost:8000/dataset/upload/', { method: 'POST', body: formData });
  //   const models = await fetchedModels.json();
  //   setModels(models.models);
  // };
  const handleFileSelect = async (e) => {
    // setFile(e.target.files[0]);
    const formData = new FormData();
    formData.append('file', e.target.files[0]);
    const fetchedModels = await fetch('http://localhost:8000/dataset/upload/', { method: 'POST', body: formData });
    const models = await fetchedModels.json();
    const sessionId = 0;
    const fetchedTask = await fetch(`http://localhost:8000/dataset/task_name/${sessionId}`);
    const task = await fetchedTask.json();
    setTaskName(task);
    setModels(models.models);
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
