import React, { useState, useEffect } from 'react';
import PropTypes from 'prop-types';
import {
  StyledButton,
  SubTitle,
  P,
  ErrorMessageDiv,
} from '../styles/globalComponents';
import { generateTooltip } from './ParameterForm';
import * as S from '../styles/components/SchemaListStyles';

function SchemaList({
  schemaType,
  schemaName,
  itemsName,
  description,
  showModal,
  handleModalClose,
  handleBack,
  outputData,
}) {
  const [list, setList] = useState([]);
  const schemaRoute = `${schemaType}/${schemaName}`;
  const [itemsToShow, setItemsToShow] = useState();
  const [selectedItem, setSelectItem] = useState();
  const [showSelectError, setSelectError] = useState(false);
  useEffect(() => {
    async function fetchList() {
      const response = await fetch(`${process.env.REACT_APP_SELECT_SCHEMA_ENDPOINT + schemaRoute}`);
      if (!response.ok) {
        throw new Error('Data could not be obtained.');
      } else {
        const schema = await response.json();
        setList(schema[schemaName]);
      }
    }
    fetchList();
  }, []);
  useEffect(() => {
    if (selectedItem !== undefined) {
      setSelectError(false);
    }
  }, [selectedItem]);
  const filterItems = (e) => {
    const search = e.target.value.toLowerCase();
    const filteredItems = list.filter((item) => item.name.toLowerCase().includes(search));
    setItemsToShow(filteredItems);
  };
  const displayImages = (images) => {
    const imageElements = images.map((img, i) => (
      <img
        src={img}
        alt={`${selectedItem.name} info ${i}`}
        style={{ borderRadius: '10px', maxWidth: '400px' }}
      />
    ));
    return (
      <div style={
        {
          display: 'flex',
          flexWrap: 'wrap',
          justifyContent: 'center',
          alignItems: 'center',
          marginBottom: '20px',
        }
      }
      >
        {imageElements}
      </div>
    );
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
    if (selectedItem !== undefined) {
      outputData(selectedItem.class);
      handleModalClose();
    } else {
      setSelectError(true);
    }
  };
  return (
    <S.Modal show={showModal} onHide={handleClose}>
      <S.Modal.Header>
        <button
          type="button"
          className="bg-transparent"
          onClick={() => {
            handleBack();
            setSelectItem(undefined);
          }}
          style={{ float: 'left', border: 'none', marginLeft: '10px' }}
        >
          <img
            alt=""
            src="images/back.svg"
            width="30"
            height="30"
          />
        </button>
        <SubTitle style={{ marginRight: '30px' }}>{`Select a ${itemsName}`}</SubTitle>
        <P>{description}</P>
      </S.Modal.Header>
      <S.Modal.Body>
        <div className="row">
          <div className="col-md-5">
            <S.SearchBar type="text" placeholder="Search ..." onChange={(e) => filterItems(e)} />
            <S.TableWrapper>
              <S.Table>
                <tbody>
                  {(
                  (itemsToShow === undefined ? list : itemsToShow).map((item) => (
                    <S.Tr key={item.class} onClick={() => handleItemClick(item)}>
                      <S.Td>{item.name}</S.Td>
                      <S.Td>{generateTooltip(item.help)}</S.Td>
                    </S.Tr>
                  )))}
                </tbody>
              </S.Table>
            </S.TableWrapper>
          </div>
          <div className="col-md-7">
            <S.InfoPanel>
              {selectedItem !== undefined ? (
                <div>
                  <p>{selectedItem.name}</p>
                  <hr />
                  {selectedItem.images === undefined ? null : displayImages(selectedItem.images)}
                  <p>{selectedItem.description}</p>
                </div>
              ) : <p>Select an option to know more!</p>}
            </S.InfoPanel>
          </div>
        </div>
      </S.Modal.Body>
      <S.Modal.Footer>
        { showSelectError ? (
          <ErrorMessageDiv style={{ marginTop: '5px', marginRight: '20px' }}>
            Select a item to continue!
          </ErrorMessageDiv>
        ) : null }
        <StyledButton onClick={handleOk}>Next</StyledButton>
      </S.Modal.Footer>
    </S.Modal>
  );
}

SchemaList.propTypes = {
  schemaType: PropTypes.string.isRequired,
  schemaName: PropTypes.string.isRequired,
  itemsName: PropTypes.string.isRequired,
  description: PropTypes.string.isRequired,
  showModal: PropTypes.bool.isRequired,
  handleModalClose: PropTypes.func.isRequired,
  handleBack: PropTypes.func.isRequired,
  outputData: PropTypes.func.isRequired,
};
export default SchemaList;
