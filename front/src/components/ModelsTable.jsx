import React from 'react';
import PropTypes from 'prop-types';
import uuid from 'react-uuid';
import { StyledButton } from '../styles/globalComponents';
import * as S from '../styles/components/ModelsTableStyles';

function ModelsTable({
  rows,
  renderFormFactory,
  removeModelFactory,
}) {
  if (rows.length > 0) {
    return (
      <S.Table bordered>
        <thead>
          <S.Tr>
            <S.Th>#</S.Th>
            <S.Th>Name</S.Th>
            <S.Th>Type</S.Th>
            <S.Th>Parameters</S.Th>
            <S.Th>Remove</S.Th>
          </S.Tr>
        </thead>

        <tbody>
          {rows.map(
            (key, index) => (
              <S.Tr key={uuid()}>
                <S.Td>{index}</S.Td>
                <S.Td>{key.name}</S.Td>
                <S.Td>{key.type}</S.Td>
                <S.Td>
                  <StyledButton
                    variant="dark"
                    onClick={renderFormFactory(key.type, index)}
                  >
                    Configure
                  </StyledButton>
                </S.Td>
                <S.Td>
                  <StyledButton
                    variant="dark"
                    onClick={removeModelFactory(index)}
                    style={{ verticalAlign: 'middle' }}
                  >
                    <img
                      alt=""
                      style={{ marginBottom: '100px' }}
                      src="images/trash-solid.svg"
                      width="40"
                      height="40"
                    />
                  </StyledButton>
                </S.Td>
              </S.Tr>
            ),
          )}
        </tbody>
      </S.Table>
    );
  }
  return (<div />);
}

ModelsTable.propTypes = {
  rows: PropTypes.arrayOf(PropTypes.objectOf(PropTypes.string)).isRequired,
  renderFormFactory: PropTypes.func.isRequired,
  removeModelFactory: PropTypes.func.isRequired,
};

export default ModelsTable;
