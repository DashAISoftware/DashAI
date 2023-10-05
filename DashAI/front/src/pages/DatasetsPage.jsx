import React, { useState } from "react";
import DatasetsTable from "../components/datasets/DatasetsTable";
import DatasetModal from "../components/datasets/DatasetModal";
import CustomLayout from "../components/custom/CustomLayout";

function DatasetsPage() {
  const [open, setOpen] = useState(false);
  const [updateTableFlag, setUpdateTableFlag] = useState(false);

  const handleNewDataset = () => {
    setOpen(true);
  };

  return (
    <CustomLayout>
      <DatasetsTable
        handleNewDataset={handleNewDataset}
        updateTableFlag={updateTableFlag}
        setUpdateTableFlag={setUpdateTableFlag}
      />
      <DatasetModal
        open={open}
        setOpen={setOpen}
        updateDatasets={() => setUpdateTableFlag(true)}
      />
    </CustomLayout>
  );
}

export default DatasetsPage;
