import React, { useState, useRef } from "react";
import { useNavigate } from "react-router-dom";
import PropTypes from "prop-types";
import { P, Title, Loading } from "../styles/globalComponents";
import { Button } from "@mui/material";
import * as S from "../styles/components/UploadStyles";
import Error from "./Error";

function Upload({ datasetState, setDatasetState, paramsData, taskName }) {
  /* --- NOTE ---
    Isn't used the JSON dataset with the task name in it
    anymore, the task is taken from user input now.
  */
  const [EMPTY, LOADING, LOADED] = [0, 1, 2];
  const [dragActive, setDragActive] = useState(false);
  const [error, setError] = useState(false);
  const [errorMessage, setErrorMessage] = useState(false);
  const inputRef = useRef(null);
  const uploadFile = async (file) => {
    setDatasetState(LOADING);
    const formData = new FormData();
    const dataloaderName = paramsData?.dataloader_params.name;
    formData.append(
      "params",
      JSON.stringify({
        ...paramsData,
        dataset_name: dataloaderName !== "" ? dataloaderName : file?.name,
      })
    );
    formData.append("url", ""); // TODO: url handling
    formData.append("file", file);
    try {
      const fetchedModels = await fetch(
        `${process.env.REACT_APP_DATASET_UPLOAD_ENDPOINT}`,
        { method: "POST", body: formData }
      );

      const models = await fetchedModels.json();
      if (typeof models.message !== "undefined") {
        setError(true);
        setErrorMessage(JSON.stringify(models));
      } else {
        localStorage.setItem("compatibleModels", JSON.stringify(models));
        setDatasetState(LOADED);
      }
    } catch (e) {
      setError(true);
      setErrorMessage("Failed request to API");
    }
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
      uploadFile(e.target.files[0]);
    }
  };
  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (datasetState === EMPTY) {
      setDragActive(false);
      if (e.dataTransfer.files && e.dataTransfer.files[0]) {
        uploadFile(e.dataTransfer.files[0]);
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
            <Button variant="outlined" onClick={handleButtonClick}>
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

  const resetData = () => {
    localStorage.clear();
    window.location.reload(false);
  };
  const navigate = useNavigate();
  const goNextStep = () => {
    navigate("/app/experiment");
  };
  if (error) {
    return <Error message={errorMessage} />;
  }
  return (
    <div>
      <Title>Load Dataset</Title>
      <br />
      <br />
      <P>{stateText(datasetState)}</P>
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
      <br />
      {taskName !== "" && (
        <P
          style={{ fontSize: "18px", lineHeight: "22.5px" }}
        >{`Task Type: ${taskName}`}</P>
      )}
      <br />
      {datasetState === LOADED && (
        <div style={{ flexDirection: "row" }}>
          <Button
            variant="outlined"
            onClick={resetData}
            style={{ marginRight: "10px" }}
          >
            Reset
          </Button>
          <Button
            variant="outlined"
            onClick={goNextStep}
            style={{ marginRight: "10px" }}
          >
            Next
          </Button>
        </div>
      )}
    </div>
  );
}

Upload.propTypes = {
  datasetState: PropTypes.number.isRequired,
  setDatasetState: PropTypes.func.isRequired,
  paramsData: PropTypes.objectOf(
    PropTypes.oneOfType([
      PropTypes.string,
      PropTypes.number,
      PropTypes.bool,
      PropTypes.object,
    ])
  ).isRequired,
  taskName: PropTypes.string,
};
Upload.defaultProps = {
  taskName: "",
};
export default Upload;
