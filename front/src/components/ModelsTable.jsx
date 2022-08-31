import React from 'react';
import { Table, Button } from 'react-bootstrap';
import PropTypes from 'prop-types';
import uuid from 'react-uuid';

function handleClickFactory(modelType, setParameterSchema) {
  return (
    async () => {
      const fetchedForm = await fetch(`http://localhost:8000/selectModel/${modelType}`);
      const formJson = await fetchedForm.json();
      setParameterSchema(formJson);
    }
  );
}
function TableRow({
  type,
  idx,
  name,
  setParameterSchema,
}) {
  TableRow.propTypes = {
    type: PropTypes.string.isRequired,
    idx: PropTypes.number.isRequired,
    name: PropTypes.string.isRequired,
    setParameterSchema: PropTypes.func.isRequired,
  };
  return (
    <tr>
      <td>{idx}</td>
      <td>{name}</td>
      <td>{type}</td>
      <td>
        <Button variant="dark" onClick={handleClickFactory(type, setParameterSchema)}>Configure</Button>
      </td>
    </tr>
  );
}
function ModelsTable({ rows, setParameterSchema }) {
  ModelsTable.propTypes = {
    rows: PropTypes.arrayOf(PropTypes.objectOf(PropTypes.string)).isRequired,
    setParameterSchema: PropTypes.func.isRequired,
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
              <TableRow
                key={uuid()}
                type={key.type}
                idx={index}
                name={key.name}
                setParameterSchema={setParameterSchema}
              />
            ),
          )}
        </tbody>
      </Table>
    );
  }
  return (<div />);
}

export default ModelsTable;
