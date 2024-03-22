import PropTypes from "prop-types";
import React, { useEffect, useState } from "react";
import { DataGrid } from "@mui/x-data-grid";
import useDatasets from "../../../hooks/useDatasets";
import { datasetsColumns } from "../constants/table";
import ExperimentsCreateDatasetStepLayout from "./ExperimentsCreateDatasetStepLayout";

function ExperimentsCreateDatasetStep({ newExp, setNewExp, setNextEnabled }) {
  const [datasetsSelected, setDatasetsSelected] = useState([]);

  const { datasets, loading } = useDatasets();

  // autoselect dataset and enable next button if some dataset was selected previously.
  useEffect(() => {
    if (typeof newExp.dataset === "object" && newExp.dataset !== null) {
      const taskEqualToExpDataset = datasets.map(
        (dataset) => newExp.dataset.id === dataset.id,
      );
      const indexOfTrue = taskEqualToExpDataset.indexOf(true);
      if (indexOfTrue !== -1) {
        setNextEnabled(true);
        setDatasetsSelected([indexOfTrue + 1]);
      }
    } else {
      setDatasetsSelected([]);
    }
  }, [datasets]);

  useEffect(() => {
    if (datasetsSelected.length > 0) {
      // the index of the table start with 1!
      // const dataset = datasets[datasetsSelected[0] - 1];
      const selectedDatasetId = datasetsSelected[0];
      const dataset = datasets.find(
        (dataset) => dataset.id === selectedDatasetId,
      );
      setNewExp({ ...newExp, dataset });
      setNextEnabled(true);
    }
  }, [datasetsSelected]);

  const isEmpty = datasets.length === 0 && !loading;
  return (
    <ExperimentsCreateDatasetStepLayout isEmpty={isEmpty}>
      <DataGrid
        rows={datasets}
        columns={datasetsColumns}
        initialState={{
          pagination: {
            paginationModel: {
              pageSize: 10,
            },
          },
        }}
        onRowSelectionModelChange={(newRowSelectionModel) => {
          setDatasetsSelected(newRowSelectionModel);
        }}
        rowSelectionModel={datasetsSelected}
        density="compact"
        pageSizeOptions={[10]}
        loading={loading}
        autoHeight
        hideFooterSelectedRowCount
      />
    </ExperimentsCreateDatasetStepLayout>
  );
}

ExperimentsCreateDatasetStep.propTypes = {
  newExp: PropTypes.shape({
    id: PropTypes.string,
    name: PropTypes.string,
    dataset: PropTypes.object,
    task_name: PropTypes.string,
    step: PropTypes.string,
    created: PropTypes.instanceOf(Date),
    last_modified: PropTypes.instanceOf(Date),
    runs: PropTypes.array,
  }),
  setNewExp: PropTypes.func.isRequired,
  setNextEnabled: PropTypes.func.isRequired,
};
export default ExperimentsCreateDatasetStep;
