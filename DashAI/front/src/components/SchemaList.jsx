import React, { useState, useEffect } from "react";
import {
  Modal,
  Card,
  CardContent,
  Input,
  TableBody,
  TableCell,
  TableRow,
  Button,
} from "@mui/material";
import SearchIcon from "@mui/icons-material/Search";
import PropTypes from "prop-types";
import {
  // StyledButton,
  SubTitle,
  P,
  ErrorMessageDiv,
} from "../styles/globalComponents";
import { generateTooltip } from "./ParameterForm";
import * as S from "../styles/components/SchemaListStyles";
import { getSchema as getSchemaRequest } from "../api/oldEndpoints";
function SchemaList({
  schemaType,
  schemaName,
  itemsName,
  description,
  showModal,
  onModalClose,
  onBack,
  outputData,
}) {
  /* Build a list with description view from a JSON schema with the list */
  const [list, setList] = useState([]);
  const [itemsToShow, setItemsToShow] = useState();
  const [selectedItem, setSelectItem] = useState();
  const [showSelectError, setSelectError] = useState(false);
  useEffect(() => {
    /* Obtain the schema of the list to show */
    async function getSchema() {
      try {
        const schema = await getSchemaRequest(schemaType, schemaName);
        setList(schema[schemaName]);
      } catch (error) {
        console.error(error);
      }
    }
    getSchema();
  }, []);
  useEffect(() => {
    /* Hide error when press 'next' button without selected an item */
    if (selectedItem !== undefined) {
      setSelectError(false);
    }
  }, [selectedItem]);
  const filterItems = (e) => {
    /* Filter items for search bar */
    const search = e.target.value.toLowerCase();
    const filteredItems = list.filter((item) =>
      item.name.toLowerCase().includes(search)
    );
    setItemsToShow(filteredItems);
  };
  const displayImages = (images) => {
    /* Display images of description */
    const imageElements = images.map((img, i) => (
      <img
        src={img}
        alt={`${selectedItem.name} info ${i}`}
        key={img}
        style={{ borderRadius: "10px", maxWidth: "400px" }}
      />
    ));
    return (
      <div
        style={{
          display: "flex",
          flexWrap: "wrap",
          justifyContent: "center",
          alignItems: "center",
          marginBottom: "20px",
        }}
      >
        {imageElements}
      </div>
    );
  };
  const handleClose = () => {
    onModalClose();
    setItemsToShow(list);
    setSelectItem(undefined);
  };
  const handleItemClick = (data) => {
    setSelectItem(data);
  };
  const handleOk = () => {
    if (selectedItem !== undefined) {
      outputData(selectedItem.class);
      onModalClose();
    } else {
      setSelectError(true);
    }
  };
  return (
    <Modal open={showModal} onClose={handleClose} sx={{ top: 50, left: 200 }}>
      <Card
        variant="outlined"
        sx={{
          padding: "10px",
          backgroundColor: "#282a30",
          maxWidth: "70vw",
        }}
      >
        <CardContent
          sx={{ textAlign: "center", display: "block", padding: "25px" }}
        >
          <button
            type="button"
            className="bg-transparent"
            onClick={() => {
              onBack();
              setSelectItem(undefined);
            }}
            style={{ float: "left", border: "none", marginLeft: "10px" }}
          >
            <img alt="" src="/images/back.svg" width="30" height="30" />
          </button>
          <SubTitle
            style={{ marginRight: "30px" }}
          >{`Select a ${itemsName}`}</SubTitle>
          <P>{description}</P>
          <div className="row">
            <div className="col-md-5">
              <S.SearchBar>
                <SearchIcon sx={{ width: "10%" }} />
                <Input
                  placeholder="Search ..."
                  onChange={(e) => filterItems(e)}
                  sx={{ width: "75%" }}
                />
              </S.SearchBar>
              {/* <S.SearchBar2
                type="text"
                placeholder="Search ..."
                onChange={(e) => filterItems(e)}
              /> */}
              <S.TableWrapper>
                <S.Table>
                  <TableBody>
                    {(itemsToShow === undefined ? list : itemsToShow).map(
                      (item) => (
                        <TableRow
                          hover
                          key={item.class}
                          onClick={() => handleItemClick(item)}
                        >
                          <TableCell>{item.name}</TableCell>
                          <TableCell>
                            <div style={{ float: "right" }}>
                              {generateTooltip(item.help)}
                            </div>
                          </TableCell>
                        </TableRow>
                      )
                    )}
                  </TableBody>
                </S.Table>
              </S.TableWrapper>
            </div>
            <div className="col-md-7">
              <S.InfoPanel>
                {selectedItem !== undefined ? (
                  <div>
                    <p>{selectedItem.name}</p>
                    <hr />
                    {selectedItem.images === undefined
                      ? null
                      : displayImages(selectedItem.images)}
                    <p>{selectedItem.description}</p>
                  </div>
                ) : (
                  <p>Select an option to know more!</p>
                )}
              </S.InfoPanel>
            </div>
          </div>
          {showSelectError ? (
            <ErrorMessageDiv style={{ marginTop: "5px", marginRight: "20px" }}>
              Select an item to continue!
            </ErrorMessageDiv>
          ) : null}
          <Button
            variant="outlined"
            sx={{ float: "right", marginTop: "20px" }}
            onClick={handleOk}
          >
            Next
          </Button>
        </CardContent>
      </Card>
    </Modal>
  );
}

SchemaList.propTypes = {
  schemaType: PropTypes.string.isRequired,
  schemaName: PropTypes.string.isRequired,
  itemsName: PropTypes.string.isRequired,
  description: PropTypes.string.isRequired,
  showModal: PropTypes.bool.isRequired,
  onModalClose: PropTypes.func.isRequired,
  onBack: PropTypes.func.isRequired,
  outputData: PropTypes.func.isRequired,
};
export default SchemaList;
