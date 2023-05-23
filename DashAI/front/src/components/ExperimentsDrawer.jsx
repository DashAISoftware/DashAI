import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  Drawer,
  Box,
  IconButton,
  Typography,
  List,
  ListItem,
  TextField,
  InputAdornment,
  CircularProgress,
  ListItemButton,
  ListItemText,
} from "@mui/material";
import MenuIcon from "@mui/icons-material/Menu";
import ClearIcon from "@mui/icons-material/Clear";
import { getExperiments as getExperimentsRequest } from "../api/experiment";
import { useSnackbar } from "notistack";

function ExperimentsDrawer() {
  const { enqueueSnackbar } = useSnackbar();
  const navigate = useNavigate();

  const [open, setOpen] = useState(false);
  const [experiments, setExperiments] = useState([]);
  const [displayedExperiments, setDisplayedExperiments] = useState(
    experiments.map(() => true),
  );
  const [searchField, setSearchField] = useState("");
  const [loading, setLoading] = useState(false);
  const [selectedExperimentIndex, setSelectedExperimentIndex] = useState(null);

  const handleExperimentsListItemClick = (event, index) => {
    setSelectedExperimentIndex(index);
    navigate(`/app/results/experiments/${experiments[index].id}`);
  };

  const handleClearSearchField = (event) => {
    setSearchField("");
    setDisplayedExperiments(experiments.map(() => true));
  };

  const handleSearchFieldChange = (event) => {
    setSearchField(event.target.value);
    setDisplayedExperiments(
      experiments.map((val) =>
        val.name.toLowerCase().includes(event.target.value.toLowerCase()),
      ),
    );
  };

  const getExperiments = async () => {
    setLoading(true);
    try {
      const experiments = await getExperimentsRequest();
      setExperiments(experiments);
      setDisplayedExperiments(experiments.map(() => true));
    } catch (error) {
      enqueueSnackbar("Error while trying to obtain the experiment table.", {
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
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    getExperiments();
  }, []);

  return (
    <React.Fragment>
      <IconButton
        size="large"
        edge="start"
        color="inherit"
        onClick={() => setOpen(true)}
      >
        <MenuIcon />
      </IconButton>
      <Drawer anchor="left" open={open} onClose={() => setOpen(false)}>
        <Box pt={2} textAlign="center" role="presentation">
          <Typography variant="h6" component="div" sx={{ mb: 2 }}>
            Experiments
          </Typography>
          <List sx={{ width: "100%" }} dense>
            <ListItem disablePadding>
              <TextField
                id="experiment-search-input"
                label="Search experiment"
                type="search"
                variant="standard"
                value={searchField}
                onChange={handleSearchFieldChange}
                fullWidth
                size="small"
                sx={{ mb: 2 }}
                InputProps={{
                  endAdornment: (
                    <InputAdornment
                      position="end"
                      onClick={handleClearSearchField}
                    >
                      <IconButton>
                        <ClearIcon />
                      </IconButton>
                    </InputAdornment>
                  ),
                }}
              />
            </ListItem>

            {/* Loading item (activated when useEffect is requesting the task list) */}
            {loading && (
              <ListItem sx={{ display: "flex", justifyContent: "center" }}>
                <CircularProgress color="inherit" />
              </ListItem>
            )}
            {/* Rendered experiments */}
            {experiments.map((experiment, index) => {
              return (
                <div key={index}>
                  {displayedExperiments}
                  <ListItem
                    key={`experiment-list-button-${experiment.name}`}
                    disablePadding
                    sx={{
                      display: displayedExperiments[index] ? "show" : "none",
                    }}
                  >
                    <ListItemButton
                      selected={selectedExperimentIndex === index}
                      onClick={(event) =>
                        handleExperimentsListItemClick(event, index)
                      }
                    >
                      <ListItemText primary={experiment.name} />
                    </ListItemButton>
                  </ListItem>
                </div>
              );
            })}
          </List>
        </Box>
      </Drawer>
    </React.Fragment>
  );
}

export default ExperimentsDrawer;
