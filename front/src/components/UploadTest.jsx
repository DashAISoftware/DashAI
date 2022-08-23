import React, { useState } from 'react';
import Form from 'react-bootstrap/Form';

function Upload() {
  const [file, setFile] = useState(null);
  const handleSubmit = async (e) => {
    e.preventDefault();

    const formData = new FormData();
    formData.append('file', file);
    fetch('http://localhost:8000/upload', { method: 'POST', body: formData });
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
