import React, { useState, useEffect } from 'react';
import PropTypes from 'prop-types';
import { StyledButton, SubTitle, P } from '../styles/globalComponents';
import { generateTooltip } from './ParameterForm';
import * as S from '../styles/components/SchemaListStyles';

function SchemaList({
  schemaType,
  schemaName,
  description,
  showModal,
  handleModalClose,
  output,
}) {
  const [list, setList] = useState([]);
  const schemaRoute = `${schemaType}/${schemaName}`;
  const [itemsToShow, setItemsToShow] = useState();
  const [selectedItem, setSelectItem] = useState();
  useEffect(() => {
    async function fetchList() {
      const response = await fetch(`${process.env.REACT_APP_SELECT_SCHEMA_ENDPOINT + schemaRoute}`);
      if (!response.ok) {
        throw new Error('Data could not be obtained.');
      } else {
        const model = await response.json();
        setList(model[schemaName]);
      }
    }
    fetchList();
  }, []);
  const filterItems = (e) => {
    const search = e.target.value.toLowerCase();
    const filteredItems = list.filter((item) => item.name.toLowerCase().includes(search));
    setItemsToShow(filteredItems);
  };
  const handleClose = () => {
    handleModalClose();
    setItemsToShow(list);
    setSelectItem(undefined);
  };
  const handleItemClick = (data) => {
    setSelectItem(data);
  };
  const handleOk = () => {
    output(selectedItem.class);
    handleModalClose();
  };
  return (
    <S.Modal show={showModal} onHide={handleClose}>
      <S.Modal.Header>
        <SubTitle>{`Select a ${schemaType}`}</SubTitle>
        <P>{description}</P>
      </S.Modal.Header>
      <S.Modal.Body>
        <S.SearchBar
          type="text"
          placeholder={`Search ${schemaType} ...`}
          onChange={(e) => filterItems(e)}
        />
        <S.TableWrapper>
          <S.Table>
            <tbody>
              {(
              (itemsToShow === undefined ? list : itemsToShow).map((item) => (
                <S.Tr key={item.class} onClick={() => handleItemClick(item)}>
                  <S.Td>{item.name}</S.Td>
                  <S.Td>{generateTooltip(item.description)}</S.Td>
                </S.Tr>
              )))}
            </tbody>
          </S.Table>
        </S.TableWrapper>
        <S.InfoPanel>
          <p>{(selectedItem === undefined ? null : selectedItem.name)}</p>
          <p>{(selectedItem === undefined ? 'Select one to know more!' : selectedItem.description)}</p>
        </S.InfoPanel>
      </S.Modal.Body>
      <S.Modal.Footer>
        <StyledButton onClick={handleOk}>Ok</StyledButton>
      </S.Modal.Footer>
    </S.Modal>
  );
}

SchemaList.propTypes = {
  schemaType: PropTypes.string.isRequired,
  schemaName: PropTypes.string.isRequired,
  description: PropTypes.string.isRequired,
  showModal: PropTypes.bool.isRequired,
  handleModalClose: PropTypes.func.isRequired,
  output: PropTypes.func.isRequired,
};
export default SchemaList;
