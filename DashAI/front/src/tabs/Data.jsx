import React, { useState } from "react";
import { Container } from "@mui/material";
import DatasetsTable from "../components/DatasetsTable";
import DatasetModal from "../components/datasets/DatasetModal";

function Data() {
  const [open, setOpen] = useState(false);
  const [updateTableFlag, setUpdateTableFlag] = useState(false);

  const handleNewDataset = () => {
    setOpen(true);
  };

  return (
    <Container>
      <DatasetsTable
        handleNewDataset={handleNewDataset}
        updateFlag={updateTableFlag}
        setUpdateFlag={setUpdateTableFlag}
      />
      <DatasetModal
        open={open}
        setOpen={setOpen}
        updateDatasets={() => setUpdateTableFlag(true)}
      />
    </Container>
  );
}

export default Data;
