import React, { useState } from "react";
import PropTypes from "prop-types";
import {
  Dialog,
  DialogTitle,
  Divider,
  IconButton,
  Grid,
  Button,
  Typography
} from "@mui/material";
import VisibilityIcon from "@mui/icons-material/Visibility";
import CustomLayout from "../custom/CustomLayout";
import RunsTable from "./RunsTable";
import RunsGraphs from "./RunsGraphs";
import useMediaQuery from "@mui/material/useMediaQuery";
import { useTheme } from "@mui/material/styles";

function RunInfo({ experiment }) {
  const [open, setOpen] = useState(false);
  const [showTable, setShowTable] = useState(true);

  const theme = useTheme();
  const screenSm = useMediaQuery(theme.breakpoints.down("sm"));

  const handleOpen = () => {
    setOpen(true);
  };

  const handleClose = () => {
    setOpen(false);
  };

  const handleShowTable = () => {
    setShowTable(true);
  };

  const handleShowGraphs = () => {
    setShowTable(false);
  };

  return (
    <React.Fragment>
      <IconButton onClick={handleOpen}>
        <VisibilityIcon />
      </IconButton>
      <Dialog
        open={open}
        fullScreen={screenSm}
        fullWidth
        maxWidth={"lg"}
        onClose={handleClose}
        PaperProps={{
            sx: {
                minHeight: "90vh",
                overflow: "auto",
                maxHeight: "90vh",
              },
        }}
      >
        <DialogTitle>{`Experiment ${experiment.name} results`}</DialogTitle>
        <Divider />
        <Grid container direction="column" alignItems="center">
          <Grid item container justifyContent="flex-start" sx={{ mt: 2, mb: 1}}>
            <Grid item sx={{ ml: 2 }}>
              <Typography variant="body1">View results as columns or graphs</Typography>
            </Grid>
          </Grid>
          <Grid item sx={{ my: 1 }}>
            <Grid container justifyContent="center">
                <Button 
                    variant="contained" 
                    color={showTable ? "primary" : "inherit"} 
                    onClick={handleShowTable} 
                    style={{
                        border: showTable ? "2px solid #00bebb" : "2px solid #00bebb" ,
                        color: showTable ? "#ffffff" : "#00bebb",
                        borderRadius: "1px"
                    }}
                >
                    Columns
                </Button>
                <Button 
                    variant="contained" 
                    color={!showTable ? "primary" : "inherit"} 
                    onClick={handleShowGraphs} 
                    style={{
                        border: !showTable ? "2px solid #00bebb" : "2px solid #00bebb" ,
                        color: !showTable ? "#ffffff" : "#00bebb",
                        borderRadius: "1px"
                    }}
                >
                    Graphs
                </Button>
            </Grid>
          </Grid>
        </Grid>
        {/* <Grid item sx={{ my: 1 }}> */}
          <Divider />
        {/* </Grid> */}
        <Grid item xs={10}>
          <CustomLayout>
            {showTable ? <RunsTable experimentId={experiment.id.toString()} /> : null}
            {!showTable ? <RunsGraphs experimentId={experiment.id} /> : null}
          </CustomLayout>
        </Grid>
      </Dialog>
    </React.Fragment>
  );
}

RunInfo.propTypes = {
  experiment: PropTypes.shape({
    name: PropTypes.string,
    id: PropTypes.number,
  }).isRequired,
};

export default RunInfo;
