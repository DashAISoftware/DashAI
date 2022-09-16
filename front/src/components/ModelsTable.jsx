import React from 'react';
import { Table, Button } from 'react-bootstrap';
import PropTypes from 'prop-types';
import uuid from 'react-uuid';

function handleClickFactory(modelType, setParameterSchema, setShowForm) {
  return (
    async () => {
      const fetchedForm = await fetch(`http://localhost:8000/selectModel/${modelType}`);
      const formJson = await fetchedForm.json();
      setParameterSchema(formJson);
      setShowForm(false);
    }
  );
}
function ModelsTable({ rows, setParameterSchema, setShowForm }) {
  ModelsTable.propTypes = {
    rows: PropTypes.arrayOf(PropTypes.objectOf(PropTypes.string)).isRequired,
    setParameterSchema: PropTypes.func.isRequired,
    setShowForm: PropTypes.func.isRequired,
  };
  if (rows.length > 0) {
    return (
      <Table stripped="true" bordered>
        <thead>
          <tr>
            <th>#</th>
            <th>Name</th>
            <th>Type</th>
            <th>Parameters</th>
          </tr>
        </thead>

        <tbody>
          {rows.map(
            (key, index) => (
              <tr key={uuid()}>
                <td>{index}</td>
                <td>{key.name}</td>
                <td>{key.type}</td>
                <td>
                  <Button
                    variant="dark"
                    onClick={handleClickFactory(key.type, setParameterSchema, setShowForm)}
                  >
                    Configure
                  </Button>
                </td>
              </tr>
            ),
          )}
        </tbody>
      </Table>
    );
  }
  return (<div />);
}

export default ModelsTable;
