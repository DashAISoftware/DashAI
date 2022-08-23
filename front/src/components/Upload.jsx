import React, { useState } from 'react';
import Form from 'react-bootstrap/Form';
import PropTypes from 'prop-types';

function Upload({ setModels }) {
  Upload.propTypes = {
    setModels: PropTypes.func.isRequired,
  };
  const [file, setFile] = useState(null);
  const handleSubmit = async (e) => {
    e.preventDefault();

    const formData = new FormData();
    formData.append('file', file);
    const fetchedModels = await fetch(`http://localhost:8000/dataset/upload/${file.name}`, { method: 'POST', body: formData });
    const models = await fetchedModels.json();
    setModels(models.models);
  };

  const handleFileSelect = (e) => {
    setFile(e.target.files[0]);
  };

  return (
    <Form onSubmit={handleSubmit}>
      <Form.Group controlId="formFileLg" className="mb-3">
        <Form.Label>Upload your dataset.</Form.Label>
        <Form.Control type="file" onChange={handleFileSelect} />
        <input type="submit" value="Upload File" />
      </Form.Group>
    </Form>
  );
}

export default Upload;
