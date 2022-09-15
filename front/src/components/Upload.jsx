import React from 'react';
// import React, { useState } from 'react';
import Form from 'react-bootstrap/Form';
import PropTypes from 'prop-types';

function Upload({ setModels }) {
  Upload.propTypes = {
    setModels: PropTypes.func.isRequired,
  };
  const handleFileSelect = async (event) => {
    const formData = new FormData();
    formData.append('file', event.target.files[0]);
    try {
      const fetchedModels = await fetch(
        'http://localhost:8000/dataset/upload/',
        { method: 'POST', body: formData },
      );
      const models = await fetchedModels.json();
      if (typeof models.error !== 'undefined') {
        setModels(['none']);
        alert(`Error: ${models.error}`);
      } else {
        setModels(models.models);
      }
    } catch (error) {
      if (error.message === 'Failed to fetch') {
        alert('API connection failed');
      } else {
        throw error;
      }
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
