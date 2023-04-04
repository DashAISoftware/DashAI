import React from "react";
import PropTypes from "prop-types";
import uuid from "react-uuid";
import { StyledButton } from "../styles/globalComponents";
import * as S from "../styles/components/ExperimentsTableStyles";

function ExperimentsTable({ rows, removeExperimentFactory }) {
  if (rows.length > 0) {
    return (
      <S.Table hover>
        <thead>
          <S.Tr>
            <S.Th>#</S.Th>
            <S.Th>Name</S.Th>
            <S.Th>Created</S.Th>
            <S.Th>Edited</S.Th>
            <S.Th>Task</S.Th>
            <S.Th>Dataset</S.Th>
            <S.Th>Remove</S.Th>
          </S.Tr>
        </thead>

        <tbody>
          {rows.map((key, index) => (
            <S.Tr key={uuid()}>
              <S.Td>{index}</S.Td>
              <S.Td>{key.name}</S.Td>
              <S.Td>{key.created}</S.Td>
              <S.Td>{key.edited}</S.Td>
              <S.Td>{key.taskName}</S.Td>
              <S.Td>{key.dataset}</S.Td>
              {/* <S.Td> */}
              {/*   <StyledButton */}
              {/*     variant="dark" */}
              {/*     onClick={renderFormFactory(key.type, index)} */}
              {/*   > */}
              {/*     Configure */}
              {/*   </StyledButton> */}
              {/* </S.Td> */}
              <S.Td>
                <StyledButton
                  variant="dark"
                  onClick={removeExperimentFactory(index)}
                  style={{
                    verticalAlign: "middle",
                    backgroundColor: "#F1AE61",
                  }}
                >
                  <img
                    alt=""
                    style={{ marginBottom: "100px" }}
                    src="/images/trash.svg"
                    width="20"
                    height="20"
                  />
                </StyledButton>
              </S.Td>
            </S.Tr>
          ))}
        </tbody>
      </S.Table>
    );
  }
  return <div />;
}

ExperimentsTable.propTypes = {
  rows: PropTypes.arrayOf(PropTypes.objectOf(PropTypes.string)).isRequired,
  // renderFormFactory: PropTypes.func.isRequired,
  removeExperimentFactory: PropTypes.func.isRequired,
};

export default ExperimentsTable;
