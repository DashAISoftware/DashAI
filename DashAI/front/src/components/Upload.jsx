import React, { useState, useRef } from "react";
// import { useNavigate } from "react-router-dom";
import PropTypes from "prop-types";
import { Loading } from "../styles/globalComponents";
import * as S from "../styles/components/UploadStyles";
// import Error from "./Error";
// import { uploadDataset as uploadDatasetRequest } from "../api/datasets";
// import { useSnackbar } from "notistack";
import { Button, DialogContentText, Grid, Paper } from "@mui/material";

function Upload({ onFileUpload }) {
  /* --- NOTE ---
    Isn't used the JSON dataset with the task name in it
    anymore, the task is taken from user input now.
  */
  const [EMPTY, LOADING, LOADED] = [0, 1, 2];
  const [datasetState, setDatasetState] = useState(EMPTY);
  const [dragActive, setDragActive] = useState(false);
  const inputRef = useRef(null);
  // const { enqueueSnackbar } = useSnackbar();

  const uploadDataset = async (file) => {
    setDatasetState(LOADING);
    // temporal solution, url is not handled yet
    const url = "";
    onFileUpload(file, url);
    setDatasetState(LOADED);
    // const formData = new FormData();
    // const dataloaderName = paramsData?.dataloader_params.name;
    // formData.append(
    //   "params",
    //   JSON.stringify({
    //     ...paramsData,
    //     dataset_name: dataloaderName !== "" ? dataloaderName : file?.name,
    //   }),
    // );
    // formData.append("url", ""); // TODO: url handling
    // formData.append("file", file);
    // try {
    //   uploadDatasetRequest(formData);
    //   setDatasetState(LOADED);
    //   enqueueSnackbar("Dataset uploaded successfully", {
    //     variant: "success",
    //     anchorOrigin: {
    //       vertical: "top",
    //       horizontal: "right",
    //     },
    //   });
    // } catch (error) {
    //   console.error(error);
    //   setError(true);
    //   setErrorMessage(error);
    //   enqueueSnackbar("Error when trying to upload the dataset.", {
    //     variant: "error",
    //     anchorOrigin: {
    //       vertical: "top",
    //       horizontal: "right",
    //     },
    //   });
    // }
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

  // const resetData = () => {
  //   localStorage.clear();
  //   window.location.reload(false);
  // };
  // const navigate = useNavigate();
  // const goNextStep = () => {
  //   navigate("/app/experiment");
  // };
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
          {/* {datasetState === LOADED && (
            <div style={{ flexDirection: "row" }}>
              <StyledButton
                type="button"
                onClick={resetData}
                style={{ marginRight: "10px" }}
              >
                Reset
              </StyledButton>
              <StyledButton
                type="button"
                onClick={goNextStep}
                style={{ marginRight: "10px" }}
              >
                Next
              </StyledButton>
            </div>
          )} */}
        </Grid>
      </Grid>
    </Paper>
  );
}

Upload.propTypes = {
  onFileUpload: PropTypes.func.isRequired,
};

export default Upload;
