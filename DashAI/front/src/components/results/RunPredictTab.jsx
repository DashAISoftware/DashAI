import { useSnackbar } from "notistack";
import { DataGrid } from "@mui/x-data-grid";
import PropTypes from "prop-types";
import React, { useState, useEffect } from "react";
import { getDatatsetById as getDatasetByIdRequest } from "../../api/datasets";
 
function RunPredictTab({ runData }){
    const { enqueueSnackbar } = useSnackbar();
    // const [loading, setLoading] = useState(false);

    const getDatasetById = async (id) => {
      // setLoading(true);
      try {
        const dataset = await getDatasetByIdRequest(id);
        const featureNames = JSON.parse(dataset.feature_names);
        const features = featureNames.map((feature) => { return {field: feature, minWidth: 180, editable: true}});
        setFeatures(features);
      } catch (error) {
        enqueueSnackbar(`Error while trying to obtain data of the run id: ${id}`);
        if (error.response) {
          console.error("Response error:", error.message);
        } else if (error.request) {
          console.error("Request error", error.request);
        } else {
          console.error("Unknown Error", error.message);
        }
    } /* finally {
      setLoading(false);
    } */
  };
    useEffect(() => {
        getDatasetById(runData.experiment_id);
    }, []);

    const [features, setFeatures] = useState([]);
    const rows = [
      {
        id: 1,
        Id: "lol",
        SepalLengthCm: "c", 
        SepalWidthCm: "c",
        PetalLengthCom: "c",
        PetalWidthCm: "c",
      },
      {
        id: 2,
        Id: "lol",
        SepalLengthCm: "c", 
        SepalWidthCm: "c",
        PetalLengthCom: "c",
        PetalWidthCm: "c",
      }
    ];

    console.log("features!", features);
    console.log("rows!", rows);
    

    return (
      // <h1>hola</h1>
      <DataGrid
        editMode="row"
        rows={rows}
        columns={features}
        autoHeight
      />
    );
}

RunPredictTab.propTypes = {
    runData: PropTypes.shape({
        experiment_id: PropTypes.number,
    }),
  };

export default RunPredictTab;