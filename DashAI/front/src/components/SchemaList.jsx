import React, { useState, useEffect } from "react";
import {
  Grid,
  DialogContentText,
  Typography,
  Paper,
  List,
  ListItem,
  TextField,
  ListItemButton,
  ListItemText,
  InputAdornment,
  IconButton,
} from "@mui/material";
import { Clear as ClearIcon } from "@mui/icons-material";
import PropTypes from "prop-types";
// import {
//   // StyledButton,
//   ErrorMessageDiv,
// } from "../styles/globalComponents";
import { getTasks as getTasksRequest } from "../api/task";
import { useSnackbar } from "notistack";
import FormTooltip from "./ConfigurableObject/FormTooltip";
function SchemaList({ schemaName, itemsName, newDataset, setNewDataset }) {
  /* Build a list with description view from a JSON schema with the list */
  const [list, setList] = useState([]);
  const [itemsToShow, setItemsToShow] = useState();
  const [selectedItem, setSelectItem] = useState();
  // const [showSelectError, setSelectError] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(null);
  const { enqueueSnackbar } = useSnackbar();

  async function getTasks() {
    try {
      const tasks = await getTasksRequest();
      setList(tasks);
    } catch (error) {
      enqueueSnackbar("Error while trying to obtain available tasks", {
        variant: "error",
        anchorOrigin: {
          vertical: "top",
          horizontal: "right",
        },
      });
      if (error.response) {
        console.error("Response error:", error.message);
      } else if (error.request) {
        console.error("Request error", error.request);
      } else {
        console.error("Unkown Error", error.message);
      }
    }
  }

  async function getSchema() {
    try {
      // const schema = await getSchemaRequest(schemaType, schemaName);
      setList([
        {
          class: "CSVDataLoader",
          name: "CSV Data",
          help: "Use CSV files to upload the data. You can use a .csv file or multiple .csv files in a .zip file.",
          description:
            "You can upload your data in a .csv file or in multiple .csv files in a .zip, where you can have the definition of splits in folders as shown above. \n If you only have one file or multiple files without the folder definition for the splits, you can set them up later. \n Make sure that all the CSV files have the same features.",
          images: ["/info_images/csv_files.png"],
          type: "object",
        },
      ]); // schema[schemaName]);
    } catch (error) {
      console.error(error);
    }
  }

  useEffect(() => {
    // when it needs the tasks it requests to the /task/ endpoint.
    if (schemaName === "tasks") {
      getTasks();
      // when it needs a dataloader it requests the legacy endpoint /schema/
    } else {
      getSchema();
    }
  }, []);
  // useEffect(() => {
  //   /* Hide error when press 'next' button without selected an item */
  //   if (selectedItem !== undefined) {
  //     setSelectError(false);
  //   }
  // }, [selectedItem]);
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
  const handleListItemClick = (data, index) => {
    setSelectedIndex(index);
    setSelectItem(data);
    setNewDataset({ ...newDataset, task_name: data.class });
  };
  // const handleOk = () => {
  //   if (selectedItem !== undefined) {
  //     // outputData(selectedItem.class);
  //   } else {
  //     setSelectError(true);
  //   }
  // };
  return (
    <React.Fragment>
      <DialogContentText>
        <Typography>{`Select a ${itemsName}`}</Typography>
      </DialogContentText>
      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Paper variant="outlined" sx={{ p: 2, pt: 0 }} elevation={10}>
            <List sx={{ width: "100%" }}>
              <ListItem disablePadding>
                <TextField
                  id={`${itemsName}-search-input`}
                  defaultValue=""
                  fullWidth
                  label={`Search a ${itemsName}`}
                  type="search"
                  variant="standard"
                  onChange={filterItems}
                  size="small"
                  sx={{ mb: 2 }}
                  InputProps={{
                    endAdornment: (
                      <InputAdornment position="end" onClick={() => {}}>
                        <IconButton>
                          <ClearIcon />
                        </IconButton>
                      </InputAdornment>
                    ),
                  }}
                />
              </ListItem>
              {(itemsToShow === undefined ? list : itemsToShow).map(
                (item, index) => {
                  return (
                    <ListItem
                      key={`${itemsName}-list-button-${item.class}`}
                      disablePadding
                      // sx={{ display: displayTasks[index] ? "show" : "none" }}
                    >
                      <ListItemButton
                        selected={selectedIndex === index}
                        onClick={() => handleListItemClick(item, index)}
                      >
                        <ListItemText primary={item.name} />
                        <FormTooltip contentStr={item.help} />
                      </ListItemButton>
                    </ListItem>
                  );
                }
              )}
            </List>
          </Paper>
        </Grid>
        <Grid item xs={12} md={6}>
          <Paper
            variant="outlined"
            sx={{ p: 2, display: "flex" }}
            elevation={10}
          >
            {selectedItem !== undefined ? (
              <div>
                <Typography>{selectedItem.name}</Typography>
                <hr />
                {selectedItem.images === undefined
                  ? null
                  : displayImages(selectedItem.images)}
                <Typography>{selectedItem.description}</Typography>
              </div>
            ) : (
              <Typography>Select an option to know more!</Typography>
            )}
          </Paper>
        </Grid>
      </Grid>
      {/* {showSelectError ? (
        <ErrorMessageDiv style={{ marginTop: "5px", marginRight: "20px" }}>
          Select an item to continue!
        </ErrorMessageDiv>
      ) : null} */}
    </React.Fragment>
  );
}

SchemaList.propTypes = {
  schemaName: PropTypes.string.isRequired,
  itemsName: PropTypes.string.isRequired,
  newDataset: PropTypes.shape({ task_name: PropTypes.string }).isRequired,
  setNewDataset: PropTypes.func.isRequired,
};

export default SchemaList;
