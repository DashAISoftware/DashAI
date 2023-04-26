import React, { useState, useEffect } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import {
  Modal,
  Card,
  CardHeader,
  CardActions,
  Container,
  Box,
} from "@mui/material";
import Upload from "../components/Upload";
import DatasetsTable from "../components/DatasetsTable";
import { getDefaultValues } from "../utils/values";
import { StyledButton } from "../styles/globalComponents";
import ParamsModal from "../components/ConfigurableObject/ParamsModal";

function Data() {
  // dataset state
  const EMPTY = 0;
  const [datasetState, setDatasetState] = useState(
    JSON.parse(localStorage.getItem("datasetState")) || EMPTY
  );
  useEffect(
    () => localStorage.setItem("datasetState", JSON.stringify(datasetState)),
    [datasetState]
  );
  //
  // --- NOTE ---
  // Isn't used the JSON dataset with the task name in it anymore, now is taken from user input.
  // -----------
  // const [taskName, setTaskName] = useState(JSON.parse(localStorage.getItem('taskName')) || '');
  // useEffect(() => localStorage.setItem('taskName', JSON.stringify(taskName)), [taskName]);
  const location = useLocation();
  const taskName = location.state?.taskName; // the task selected by user
  const dataloader = location.state?.dataloader; // the dataloader selected by user
  const schemaRoute = `dataloader/${dataloader && dataloader.toLowerCase()}`; // name of the JSON schema for dataloader
  //
  const [showParams, setShowParams] = useState(location.state !== null);
  const [showUploadModal, setShowUploadModal] = useState(false);
  // const [showNameModal, setShowNameModal] = useState(location.state !== null);
  const [paramsSchema, setParamsSchema] = useState();
  // const [datasetName, setDatasetName] = useState("");
  const [submitForm, setSubmitForm] = useState({
    task_name: taskName,
    dataloader,
  });
  //
  const [showSplitsError, setSplitsError] = useState(false);
  const [showSplitConfig, setSplitConfig] = useState(false);
  const [showMoreOptions, setShowMoreOptions] = useState(false);
  //
  const [datasets, setDatasets] = useState([]);
  useEffect(() => {
    setDatasetState(EMPTY);
    async function fetchParams() {
      const response = await fetch(
        `${process.env.REACT_APP_SELECT_SCHEMA_ENDPOINT + schemaRoute}`
      );
      if (!response.ok) {
        throw new Error("Data could not be obtained.");
      } else {
        const schema = await response.json();
        setParamsSchema(schema);
      }
    }
    fetchParams();
  }, []);

  useEffect(() => {
    async function fetchDatasets() {
      const response = await fetch(
        `${process.env.REACT_APP_DATASET_UPLOAD_ENDPOINT}`
      );
      if (!response.ok) {
        throw new Error("Could not obtain datasets");
      } else {
        const fetchedDatasets = await response.json();
        setDatasets(fetchedDatasets);
      }
    }
    fetchDatasets();
  }, []);

  const handleSubmitParams = (modelName, values) => {
    /*
      How the parameters are in different sections,
      we need to join all the parameters in a single JSON
      to send to the endpoint. For that depending on the
      parameters model defined in backend (pydantic model)
      here is building that JSON of parameters.
    */
    const auxForm = submitForm;
    let sum = 0;
    const appendItemsToJSON = (object, items) => {
      for (let i = 0; i < Object.keys(items).length; i += 1) {
        const key = Object.keys(items)[i];
        const value = items[key];
        auxForm[object][key] = value;
      }
    };
    if (auxForm.splits === undefined) {
      // If user leaves the default values in split settings
      auxForm.splits = getDefaultValues(paramsSchema.splits);
      const moreOptions = getDefaultValues(paramsSchema.splits.more_options);
      appendItemsToJSON("splits", moreOptions);
    }
    switch (modelName) {
      case "splits": // Add the splits parameters
        sum = values.train_size + values.test_size + values.val_size;
        if (sum >= 0.999 && sum <= 1) {
          setSplitsError(false);
          appendItemsToJSON("splits", values);
          setSubmitForm(auxForm);
        } else {
          setSplitsError(true);
        }
        break;
      case "Advanced": // Add the more options parameters
        appendItemsToJSON("splits", values);
        setSubmitForm(auxForm);
        break;
      default: // Add the rest of parameters of principal modal
        auxForm.dataloader_params = values;
        if (values.class_column !== undefined) {
          auxForm.class_column = values.class_column;
          delete auxForm.dataloader_params.class_column;
        }
        if (values.splits_in_folders !== undefined) {
          auxForm.splits_in_folders = values.splits_in_folders;
          delete auxForm.dataloader_params.splits_in_folders;
        }
        setSubmitForm(auxForm);
    }
  };
  const navigate = useNavigate();
  const handleBackToHome = () => {
    navigate("/app", { state: { task: taskName } });
  };
  const handleNewDataset = () => {
    navigate("/app", { state: { newDataset: true } });
  };
  return (
    <Container>
      {showParams && paramsSchema ? (
        <ParamsModal
          dataloader={dataloader}
          paramsSchema={paramsSchema}
          onSubmit={handleSubmitParams}
          showModal={showParams}
          setShowModal={setShowParams}
          showSplitConfig={showSplitConfig}
          setSplitConfig={setSplitConfig}
          showMoreOptions={showMoreOptions}
          setShowMoreOptions={setShowMoreOptions}
          setShowNameModal={handleBackToHome}
          showSplitsError={showSplitsError}
          setShowUploadModal={setShowUploadModal}
        />
      ) : null}
      <Modal
        open={showUploadModal}
        onClose={() => {
          showUploadModal(false);
        }}
        style={{
          position: "absolute",
          maxWidth: "60vw",
          minHeight: "40vh",
          left: "20%",
          top: "5%",
        }}
        aria-labelledby="modal-modal-title"
        aria-describedby="modal-modal-description"
      >
        <div>
          <Card
            variant="outlined"
            style={{ padding: "10px", backgroundColor: "#282a30" }}
          >
            <CardHeader
              avatar={
                <button
                  type="button"
                  className="bg-transparent"
                  onClick={() => {
                    setShowParams(true);
                    setShowUploadModal(false);
                  }}
                  style={{ float: "left", border: "none", marginLeft: "10px" }}
                >
                  <img alt="" src="/images/back.svg" width="30" height="30" />
                </button>
              }
            />
            <Box
              sx={{
                display: "flex",
                textAlign: "center",
                justifyContent: "center",
              }}
            >
              <Upload
                datasetState={datasetState}
                setDatasetState={setDatasetState}
                paramsData={submitForm}
                taskName={taskName}
                // setTaskName={setTaskName}
              />
            </Box>
            <CardActions>
              <StyledButton
                style={{ marginLeft: "820px" }}
                onClick={() => setShowUploadModal()}
              >
                OK
              </StyledButton>
            </CardActions>
          </Card>
        </div>
      </Modal>
      <DatasetsTable
        initialRows={datasets}
        handleNewDataset={handleNewDataset}
      />
    </Container>
  );
}

export default Data;
