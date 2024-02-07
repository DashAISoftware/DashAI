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

const pluginTypes = [
  { value: "", type: "None" },
  { value: "package", type: "Package" },
  { value: "task", type: "Task" },
  { value: "dataloader", type: "Dataloader" },
  { value: "model", type: "Model" },
  { value: "metric", type: "Metric" },
];

const PluginsToolbar = ({
  cardView,
  handleCardViewChange,
  searchField,
  handleSearchFieldChange,
  type,
  handleTypeChange,
  sortBy,
  handleSortByChange,
}) => {
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
            <InputLabel id="select-type-label">Type</InputLabel>
            <Select
              id="select-type"
              value={type}
              onChange={handleTypeChange}
              label="Type"
              autoWidth
            >
              {pluginTypes.map((pluginType) => (
                <MenuItem key={pluginType.value} value={pluginType.value}>
                  {pluginType.type}
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
              <MenuItem value={"latest"}>Latest</MenuItem>
            </Select>
          </FormControl>
        </Grid>
      </Grid>
    </Grid>
  );
};

PluginsToolbar.propTypes = {
  cardView: PropTypes.bool,
  handleCardViewChange: PropTypes.func,
  searchField: PropTypes.string,
  handleSearchFieldChange: PropTypes.func,
  type: PropTypes.string,
  handleTypeChange: PropTypes.func,
  sortBy: PropTypes.string,
  handleSortByChange: PropTypes.func,
};

export default PluginsToolbar;
