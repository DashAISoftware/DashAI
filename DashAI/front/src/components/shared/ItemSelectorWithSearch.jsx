import ClearIcon from "@mui/icons-material/Clear";
import {
  Box,
  IconButton,
  InputAdornment,
  Stack,
  TextField,
} from "@mui/material";
import PropTypes from "prop-types";
import React, { useState } from "react";
import ItemSelector from "./ItemSelector";

function ItemSelectorWithSearch({ itemsList, ...props }) {
  const [searchField, setSearchField] = useState("");

  const handleSearchFieldChange = (event) => {
    setSearchField(event.target.value.toLowerCase());
  };

  const filteredItems = itemsList.filter((val) =>
    val.name.toLowerCase().includes(searchField),
  );

  return (
    <Box sx={{ p: 2 }}>
      <Stack>
        <TextField
          id="item-search-input"
          fullWidth
          label="Search..."
          type="search"
          variant="standard"
          value={searchField}
          onChange={handleSearchFieldChange}
          size="small"
          sx={{ mb: 2 }}
          InputProps={{
            endAdornment: (
              <InputAdornment position="end">
                <IconButton onClick={() => setSearchField("")}>
                  <ClearIcon />
                </IconButton>
              </InputAdornment>
            ),
          }}
        />
        <ItemSelector itemsList={filteredItems} {...props} />
      </Stack>
    </Box>
  );
}

ItemSelectorWithSearch.propTypes = {
  itemsList: PropTypes.arrayOf(PropTypes.shape({ name: PropTypes.string }))
    .isRequired,
};

export default ItemSelectorWithSearch;
