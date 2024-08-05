import React, { useState, useEffect } from "react";
import PropTypes from "prop-types";
import { Box, Dialog, DialogContent, DialogTitle, Grid } from "@mui/material";
import { useSnackbar } from "notistack";
import { getDatasetInfo as getDatasetInfoRequest } from "../../api/datasets";
import ParameterForm from "../configurableObject/ParameterForm";
import ScopeForm from "./ScopeForm";

const ConverterEditorModal = ({
  converterName,
  updateValues,
  converterSchema,
  datasetId,
  open,
  handleClose,
}) => {
  const { enqueueSnackbar } = useSnackbar();
  const [datasetInfo, setDatasetInfo] = useState({});
  const [infoLoading, setInfoLoading] = useState(true);
  const [scope, setScope] = useState({
    columns: [],
    rows: [],
  });
  const [inputError, setInputError] = useState(false);

  const getDatasetInfo = async () => {
    setInfoLoading(true);
    try {
      const datasetInfo = await getDatasetInfoRequest(datasetId);
      setDatasetInfo({ ...datasetInfo, id: datasetId });
    } catch (error) {
      enqueueSnackbar("Error while trying to obtain the dataset info.");
      if (error.response) {
        console.error("Response error:", error.message);
      } else if (error.request) {
        console.error("Request error", error.request);
      } else {
        console.error("Unknown Error", error.message);
      }
    } finally {
      setInfoLoading(false);
    }
  };

  useEffect(() => {
    getDatasetInfo();
  }, []);

  const handleOnSave = (params) => {
    if (inputError) return;
    let paramsAndScope = {
      params: params,
      scope: scope,
    };
    updateValues(paramsAndScope);
    handleClose();
    setScope({
      columns: [],
      rows: [],
    });
  };

  return (
    <React.Fragment>
      <Dialog open={open} onClose={handleClose}>
        <DialogTitle>{`${
          converterName ?? "Converter"
        } configuration`}</DialogTitle>

        <DialogContent>
          <Box sx={{ px: 4, overflow: "auto" }}>
            <Grid container direction={"column"} alignItems={"center"}>
              {/* Form for parameters */}
              {!infoLoading && converterName && (
                <ParameterForm
                  parameterSchema={converterSchema}
                  onFormSubmit={handleOnSave}
                  submitButton
                  extraOptions={
                    <ScopeForm
                      datasetInfo={datasetInfo}
                      converterName={converterName}
                      scope={scope}
                      setScope={setScope}
                      setErrors={setInputError}
                    />
                  }
                />
              )}
            </Grid>
          </Box>
        </DialogContent>
      </Dialog>
    </React.Fragment>
  );
};

ConverterEditorModal.propTypes = {
  converterName: PropTypes.string,
  updateValues: PropTypes.func.isRequired,
  converterSchema: PropTypes.object,
  datasetId: PropTypes.number.isRequired,
  open: PropTypes.bool,
  handleClose: PropTypes.func.isRequired,
};

ConverterEditorModal.defaultProps = {
  converterName: "",
  converterSchema: {},
  open: false,
};

export default ConverterEditorModal;