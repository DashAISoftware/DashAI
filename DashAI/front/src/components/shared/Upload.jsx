import React, { useState, useRef } from "react";
import PropTypes from "prop-types";
import {
  Box,
  Button,
  CircularProgress,
  DialogContentText,
  Grid,
  IconButton,
  Paper,
  Typography,
} from "@mui/material";

import TextSnippetIcon from "@mui/icons-material/TextSnippet";
import ClearIcon from "@mui/icons-material/Clear";

/**
 * Renders a drag and drop to upload a file (dataset).
 * The upload (send to API) doesn't happen here, this component just adds the file "uploaded" to the
 * newDataset state in the modal
 * @param {function} onFileUpload function to handle when the user "uploads" a dataset
 */
function Upload({ onFileUpload, emptyUploadText, multiple = false }) {
  const [EMPTY, LOADING, LOADED] = [0, 1, 2];
  const [datasetState, setDatasetState] = useState(EMPTY);
  const [dragActive, setDragActive] = useState(false);
  const [fileNames, setFileNames] = useState([]);
  const inputRef = useRef(null);

  const uploadDataset = async (files) => {
    const fileArray = Array.isArray(files) ? files : Array.from(files);
    setDatasetState(LOADING);
    const url = "";
    await onFileUpload(fileArray, url);
    setDatasetState(LOADED);
    setFileNames(fileArray.map((f) => f.name));
  };

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (datasetState === EMPTY) {
      if (e.type === "dragenter" || e.type === "dragover") {
        setDragActive(true);
      } else if (e.type === "dragleave") {
        setDragActive(false);
      }
    }
  };

  const handleSelect = (e) => {
    if (datasetState === EMPTY) {
      const files = multiple ? e.target.files : [e.target.files[0]];
      uploadDataset(files);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (datasetState === EMPTY) {
      setDragActive(false);
      const files = multiple ? e.dataTransfer.files : [e.dataTransfer.files[0]];
      if (files && files.length > 0) {
        uploadDataset(files);
      }
    }
  };

  const handleButtonClick = () => {
    inputRef.current.click();
  };

  const handleDeleteDataset = () => {
    onFileUpload(null, "");
    setDatasetState(EMPTY);
    setFileNames([]);
  };

  const stateContent = (state) => {
    switch (state) {
      case EMPTY:
        return (
          <React.Fragment>
            <Grid>
              <input
                type="file"
                ref={inputRef}
                style={{ display: "none" }}
                onChange={handleSelect}
                multiple={multiple}
              />
            </Grid>
            {dragActive ? (
              <Grid>
                <Typography variant="subtitle1">
                  Drop the file{multiple ? "s" : ""} here.
                </Typography>
              </Grid>
            ) : (
              <React.Fragment>
                <Grid>
                  <Typography variant="subtitle1">
                    Drag and drop {multiple ? "your files" : "a file"} here, or
                  </Typography>
                </Grid>
                <Grid>
                  <Button variant="contained">Upload a file</Button>
                </Grid>
              </React.Fragment>
            )}
          </React.Fragment>
        );

      case LOADING:
        return <CircularProgress color="inherit" />;

      case LOADED:
        return (
          <>
            <TextSnippetIcon sx={{ fontSize: "58px" }} />
            <Grid>
              {fileNames.map((name, index) => (
                <Typography
                  key={index}
                  variant="subtitle1"
                  sx={{
                    color: "gray",
                    textAlign: "center",
                  }}
                >
                  {name}
                </Typography>
              ))}
            </Grid>
          </>
        );
    }
  };

  return (
    <Paper
      sx={{
        p: 4,
        borderRadius: 2,
        display: "flex",
        flexDirection: "column",
        minHeight: "400px",
      }}
    >
      {/* state text */}
      <Box sx={{ textAlign: "center", mb: 2 }}>
        <DialogContentText>
          {datasetState === LOADING && "Loading..."}
          {datasetState === LOADED && "Loaded"}
          {datasetState === EMPTY && emptyUploadText}
        </DialogContentText>
      </Box>

      {/* Drag and drop */}
      <Box
        sx={{
          flex: 1,
          border: 1,
          borderRadius: 2,
          cursor: datasetState === EMPTY ? "pointer" : "auto",
          borderStyle: "dashed",
          borderColor: "divider",
          overflow: "auto",
          position: "relative",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          minHeight: "300px",
        }}
        onClick={datasetState === EMPTY ? handleButtonClick : null}
        onDragEnter={datasetState === EMPTY ? handleDrag : null}
        onDragLeave={datasetState === EMPTY ? handleDrag : null}
        onDragOver={datasetState === EMPTY ? handleDrag : null}
        onDrop={datasetState === EMPTY ? handleDrop : null}
      >
        <input
          type="file"
          ref={inputRef}
          style={{ display: "none" }}
          onChange={handleSelect}
          multiple={multiple}
        />

        <Box
          sx={{
            textAlign: "center",
            flex: 1,
            display: "flex",
            flexDirection: "column",
            justifyContent: "center",
            alignItems: "center",
          }}
        >
          {datasetState === EMPTY &&
            (dragActive ? (
              <Typography variant="subtitle1">
                Drop the file{multiple ? "s" : ""} here.
              </Typography>
            ) : (
              <>
                <Typography variant="subtitle1" sx={{ mb: 2 }}>
                  Drag and drop {multiple ? "your files" : "a file"} here, or
                </Typography>
                <Button variant="contained">Upload a file</Button>
              </>
            ))}

          {datasetState === LOADING && <CircularProgress color="inherit" />}

          {datasetState === LOADED && (
            <>
              <TextSnippetIcon sx={{ fontSize: "58px", mb: 1 }} />
              {fileNames.map((name, index) => (
                <Typography
                  key={index}
                  variant="subtitle1"
                  sx={{
                    color: "gray",
                    textAlign: "center",
                  }}
                >
                  {name}
                </Typography>
              ))}
              <IconButton
                onClick={handleDeleteDataset}
                sx={{ position: "absolute", right: 0, top: 0 }}
              >
                <ClearIcon />
              </IconButton>
            </>
          )}
        </Box>
      </Box>
    </Paper>
  );
}

Upload.propTypes = {
  onFileUpload: PropTypes.func.isRequired,
  emptyUploadText: PropTypes.oneOfType([PropTypes.string, PropTypes.node]),
};

export default Upload;
