import React, { useState, useEffect } from "react";
import { Container } from "@mui/material";
import DatasetsTable from "../components/DatasetsTable";
import DatasetModal from "../components/datasets/DatasetModal";
import { useSnackbar } from "notistack";
import { getDatasets as getDatasetsRequest } from "../api/datasets";

function Data() {
  const [datasets, setDatasets] = useState([]);
  const [open, setOpen] = useState(false);
  const { enqueueSnackbar } = useSnackbar();

  async function getDatasets() {
    try {
      const datasets = await getDatasetsRequest();
      setDatasets(datasets);
    } catch (error) {
      console.error(error);
      enqueueSnackbar("Error while trying to obtain the datasets table.", {
        variant: "error",
        anchorOrigin: {
          vertical: "top",
          horizontal: "right",
        },
      });
    }
  }
  const handleNewDataset = () => {
    setOpen(true);
  };

  useEffect(() => {
    getDatasets();
  }, []);
  return (
    <Container>
      <DatasetsTable
        initialRows={datasets}
        handleNewDataset={handleNewDataset}
        updateDatasets={getDatasets}
      />
      <DatasetModal open={open} setOpen={setOpen} />
    </Container>
  );
}

export default Data;
