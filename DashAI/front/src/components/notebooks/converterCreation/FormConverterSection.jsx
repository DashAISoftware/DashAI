import React, { useState } from "react";
import { Box } from "@mui/material";
import { saveConverter } from "../../../api/converter";
import { useExplorersAndConverters } from "../context/ExplorersAndConvertersContext";
import { useSnackbar } from "notistack";
import ParameterStepConverter from "./ParameterStepConverter";
import ScopeStepConverter from "./ScopeStepConverter";
import { startJobPolling } from "../../../utils/jobPoller";
import { enqueueConverterJob } from "../../../api/job";
import { getDatasetTypesByFilePath } from "../../../api/datasets";
import { useTranslation } from "react-i18next";

export default function FormConverterSection({
  step,
  setStep,
  handleClose,
  tool,
  notebook,
  hideButtons = false,
}) {
  const [targetColumn, setTargetColumn] = useState(null);
  const [rows, setRows] = useState([]);
  const [columns, setColumns] = useState([]);
  const {
    explorersAndConverters,
    setExplorersAndConverters,
    setColumnTypes,
    setLastAddedItemId,
  } = useExplorersAndConverters();
  const { enqueueSnackbar } = useSnackbar();
  const { t } = useTranslation(["common", "datasets"]);

  const handleSaveConverter = async (params) => {
    const data = {
      notebook_id: notebook.id,
      converter: tool.name,
      parameters: {
        params: params,
        scope: {
          columns: columns,
          rows: rows,
        },
        order: 1,
        target: targetColumn,
      },
    };

    saveConverter(data)
      .then((response) => {
        const data = { ...response, type: "converter" };
        setExplorersAndConverters((prev) => [...prev, data]);
        setLastAddedItemId({ id: data.id, type: "converter" });
        enqueueSnackbar(
          t("datasets:message.converterCreated", { name: tool.name }),
          {
            variant: "success",
          },
        );

        enqueueConverterJob(data.id)
          .then((jobResponse) => {
            if (jobResponse && jobResponse.id) {
              startJobPolling(
                jobResponse.id,

                (result) => {
                  enqueueSnackbar(
                    t("datasets:message.converterProcessed", {
                      name: tool.name,
                    }),
                    {
                      variant: "success",
                    },
                  );

                  setExplorersAndConverters((prev) =>
                    prev.map((item) =>
                      item.id === data.id && item.type === "converter"
                        ? { ...item, status: 3 }
                        : item,
                    ),
                  );

                  if (notebook?.file_path) {
                    getDatasetTypesByFilePath(notebook.file_path)
                      .then((types) => setColumnTypes(types ?? {}))
                      .catch(console.error);
                  }
                },

                (result) => {
                  console.error("Converter job failed:", result);
                  enqueueSnackbar(
                    t("datasets:error.converterFailedWithInfo", {
                      error: result.error_msg || t("common:unknownError"),
                    }),
                    { variant: "error" },
                  );

                  setExplorersAndConverters((prev) =>
                    prev.map((item) =>
                      item.id === data.id && item.type === "converter"
                        ? { ...item, status: 4 }
                        : item,
                    ),
                  );
                },
              );
            }
          })
          .catch((error) => {
            console.error("Error enqueuing converter job:", error);
            enqueueSnackbar(t("datasets:error.processConverterError"), {
              variant: "error",
            });
          });
      })
      .catch((error) => {
        console.error("Error creating converter:", error);
        enqueueSnackbar(t("datasets:error.createConverterError"), {
          variant: "error",
        });
      })
      .finally(() => {
        handleClose();
      });
  };

  return (
    <Box
      sx={{
        overflow: "visible",
        display: "flex",
        flexDirection: "column",
        flex: 1,
        maxHeight: "100%",
        minHeight: 0,
      }}
    >
      {step === 0 && (
        <ScopeStepConverter
          supervised={tool.metadata.supervised}
          targetColumn={targetColumn}
          setTargetColumn={setTargetColumn}
          tool={tool}
          rows={rows}
          setRows={setRows}
          columns={columns}
          setColumns={setColumns}
          notebook={notebook}
          nextStep={
            Object.values(tool.schema.properties).length > 0
              ? () => setStep((s) => s + 1)
              : () => handleSaveConverter({})
          }
          hideButtons={hideButtons}
        />
      )}

      {step === 1 && (
        <ParameterStepConverter
          converter={tool.name}
          tool={tool}
          selectedColumns={columns}
          initialParams={{}}
          handleSaveConverter={handleSaveConverter}
          setStep={setStep}
          hideButtons={hideButtons}
        />
      )}
    </Box>
  );
}
