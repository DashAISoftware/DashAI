import React from 'react';
import { Table, Button } from 'react-bootstrap';
import PropTypes from 'prop-types';
import uuid from 'react-uuid';

function ModelsTable({ rows, renderFormFactory }) {
  ModelsTable.propTypes = {
    rows: PropTypes.arrayOf(PropTypes.objectOf(PropTypes.string)).isRequired,
    renderFormFactory: PropTypes.func.isRequired,
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
                    onClick={renderFormFactory(key.type, index)}
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
