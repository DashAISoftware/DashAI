import React from "react";
import {
  Grid,
  ToggleButtonGroup,
  ToggleButton,
  Select,
  FormControl,
  InputLabel,
  TextField,
  MenuItem,
  InputAdornment,
} from "@mui/material";
import ViewListIcon from "@mui/icons-material/ViewList";
import ViewModuleIcon from "@mui/icons-material/ViewModule";
import SearchIcon from "@mui/icons-material/Search";
import PropTypes from "prop-types";

const sortByValues = [
  { value: "latest", label: "Latest" },
  { value: "oldest", label: "Oldest" },
];

function PluginsToolbar({
  cardView,
  handleCardViewChange,
  searchField,
  handleSearchFieldChange,
  type,
  handleTypeChange,
  sortBy,
  handleSortByChange,
  pluginTags,
}) {
  return (
    <Grid container justifyContent={"space-between"} paddingBottom={2}>
      <Grid item container xs={8} spacing={2}>
        <Grid item xs={8}>
          <TextField
            id="input-with-icon-textfield"
            label="Search"
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon />
                </InputAdornment>
              ),
            }}
            variant="outlined"
            value={searchField}
            onChange={handleSearchFieldChange}
            fullWidth
          />
        </Grid>
        <Grid item>
          <FormControl variant="outlined" sx={{ minWidth: 120 }}>
            <InputLabel id="select-type-label">Tags</InputLabel>
            <Select
              id="select-type"
              value={type}
              onChange={handleTypeChange}
              label="Type"
              autoWidth
            >
              <MenuItem key={""} value={""}>
                None
              </MenuItem>
              {pluginTags.map((pluginTag) => (
                <MenuItem key={pluginTag} value={pluginTag}>
                  {pluginTag}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </Grid>
      </Grid>

      <Grid
        item
        container
        xs={4}
        spacing={2}
        display={"flex"}
        alignItems={"center"}
        justifyContent={"flex-end"}
      >
        <Grid item>
          <ToggleButtonGroup
            value={cardView}
            exclusive
            onChange={handleCardViewChange}
            aria-label="card view mode"
          >
            <ToggleButton value={true} aria-label="grid view">
              <ViewModuleIcon />
            </ToggleButton>
            <ToggleButton value={false} aria-label="list view">
              <ViewListIcon />
            </ToggleButton>
          </ToggleButtonGroup>
        </Grid>

        <Grid item>
          <FormControl variant="outlined" sx={{ minWidth: 120 }}>
            <InputLabel id="select-sort-by-label">Sort by</InputLabel>
            <Select
              id="select-sort-by"
              value={sortBy}
              onChange={handleSortByChange}
              label="Sort by"
            >
              {sortByValues.map((sortByValue) => (
                <MenuItem key={sortByValue.value} value={sortByValue.value}>
                  {sortByValue.label}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </Grid>
      </Grid>
    </Grid>
  );
}

PluginsToolbar.propTypes = {
  cardView: PropTypes.bool.isRequired,
  handleCardViewChange: PropTypes.func.isRequired,
  searchField: PropTypes.string.isRequired,
  handleSearchFieldChange: PropTypes.func.isRequired,
  type: PropTypes.string.isRequired,
  handleTypeChange: PropTypes.func.isRequired,
  sortBy: PropTypes.string.isRequired,
  handleSortByChange: PropTypes.func.isRequired,
  pluginTags: PropTypes.array.isRequired,
};

export default PluginsToolbar;
