import React from 'react';
import { Table } from 'react-bootstrap';
import styled from 'styled-components';
import PropTypes from 'prop-types';
import uuid from 'react-uuid';
import { StyledButton } from '../styles/globalComponents';

const Th = styled.th`
  color: #fff;
`;

const Td = styled.td`
  color: #fff;
`;

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
      </Table>
    );
  }
  return (<div />);
}

export default ModelsTable;
