import React from 'react';
import Table from 'react-bootstrap/Table';

function ModelsTable() {
  return (
    <Table stripped="true" bordered hover>
      <thead>
        <tr>
          <th>#</th>
          <th>Name</th>
          <th>Type</th>
          <th>Parameters</th>
        </tr>
      </thead>

      <tbody>
        <tr>
          <td>0</td>
          <td>MyModel</td>
          <td>NumericalWrapperForText</td>
          <td>Configure</td>
        </tr>
      </tbody>
    </Table>
  );
}

export default ModelsTable;
