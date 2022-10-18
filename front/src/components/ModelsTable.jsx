import React from 'react';
import PropTypes from 'prop-types';
import uuid from 'react-uuid';
import { StyledButton } from '../styles/globalComponents';
import {
  StyledTable,
  Th,
  Td,
} from '../styles/components/ModelsTableStyles';

function ModelsTable({ rows, renderFormFactory }) {
  ModelsTable.propTypes = {
    rows: PropTypes.arrayOf(PropTypes.objectOf(PropTypes.string)).isRequired,
    renderFormFactory: PropTypes.func.isRequired,
  };
  if (rows.length > 0) {
    return (
      <StyledTable bordered>
        <thead>
          <tr>
            <Th>#</Th>
            <Th>Name</Th>
            <Th>Type</Th>
            <Th>Parameters</Th>
          </tr>
        </thead>

        <tbody>
          {rows.map(
            (key, index) => (
              <tr key={uuid()}>
                <Td>{index}</Td>
                <Td>{key.name}</Td>
                <Td>{key.type}</Td>
                <td>
                  <StyledButton
                    variant="dark"
                    onClick={renderFormFactory(key.type, index)}
                  >
                    Configure
                  </StyledButton>
                </td>
              </tr>
            ),
          )}
        </tbody>
      </StyledTable>
    );
  }
  return (<div />);
}

export default ModelsTable;
