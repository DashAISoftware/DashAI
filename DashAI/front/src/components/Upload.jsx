import React, { useState, useRef } from "react";
import PropTypes from "prop-types";
import { Loading } from "../styles/globalComponents";
import * as S from "../styles/components/UploadStyles";
import { Button, DialogContentText, Grid, Paper } from "@mui/material";

/**
 * Renders a drag and drop to upload a file (dataset).
 * The upload (send to API) doesn't happen here, this component just adds the file "uploaded" to the
 * newDataset state in the modal
 * @param {function} onFileUpload function to handle when the user "uploads" a dataset
 */
function Upload({ onFileUpload }) {
  const [EMPTY, LOADING, LOADED] = [0, 1, 2];
  const [datasetState, setDatasetState] = useState(EMPTY);
  const [dragActive, setDragActive] = useState(false);
  const inputRef = useRef(null);

  const uploadDataset = async (file) => {
    setDatasetState(LOADING);
    const url = "";
    onFileUpload(file, url);
    setDatasetState(LOADED);
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
      uploadDataset(e.target.files[0]);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (datasetState === EMPTY) {
      setDragActive(false);
      if (e.dataTransfer.files && e.dataTransfer.files[0]) {
        uploadDataset(e.dataTransfer.files[0]);
      }
    }
  };

  const handleButtonClick = () => {
    inputRef.current.click();
  };

  const stateText = (state) => {
    switch (state) {
      case EMPTY:
        return "Upload your dataset";
      case LOADING:
        return "Loading dataset";
      case LOADED:
        return "Uploaded dataset";
      default:
        return "";
    }
  };

  // renders content (images) inside the drag and drop component depending on the state of the dataset
  const stateImg = (state) => {
    switch (state) {
      case EMPTY:
        return (
          <div>
            <input
              ref={inputRef}
              id="input-upload-dataset"
              style={{ display: "none" }}
              type="file"
              onChange={handleSelect}
            />
            <p>Drag and drop your file here or</p>
            <Button variant="contained" onClick={handleButtonClick}>
              Upload a file
            </Button>
          </div>
        );
      case LOADING:
        return (
          <Loading alt="" src="/images/loading.png" width="58" height="58" />
        );
      case LOADED:
        return <img alt="" src="/images/loaded.png" width="58" height="58" />;
      default:
        return <div />;
    }
  };

  return (
    <Paper variant="outlined" sx={{ pt: 4, height: "100%" }}>
      <Grid container direction={"column"} alignItems={"center"}>
        <Grid item>
          <DialogContentText>{stateText(datasetState)}</DialogContentText>
        </Grid>
        <Grid item sx={{ pt: 3 }}>
          <S.FormFileUpload onDragEnter={handleDrag}>
            <S.LabelFileUpload
              htmlFor="input-upload-dataset"
              className={dragActive ? "drag-active" : ""}
            >
              {stateImg(datasetState)}
            </S.LabelFileUpload>
            {dragActive && (
              <S.DragFile
                onDragEnter={handleDrag}
                onDragLeave={handleDrag}
                onDragOver={handleDrag}
                onDrop={handleDrop}
              />
            )}
          </S.FormFileUpload>
        </Grid>
      </Grid>
    </Paper>
  );
}

Upload.propTypes = {
  onFileUpload: PropTypes.func.isRequired,
};

export default Upload;
