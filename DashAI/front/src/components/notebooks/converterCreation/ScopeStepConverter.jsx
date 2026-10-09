import { useState, useEffect, useMemo } from "react";
import { Box, Typography, Tooltip, IconButton } from "@mui/material";
import { useTheme } from "@mui/material/styles";
import ConverterClassColumnModal from "./ConverterTargetColumnModal";
import HelpIcon from "@mui/icons-material/Help";
import FormSchemaButtonGroup from "../../shared/FormSchemaButtonGroup";
import ColumnSelector from "../ColumnSelector";
import { RowSelector } from "../RowSelector";
import { getDatasetInfoByFilePath } from "../../../api/datasets";
import { useTourContext } from "../../tour/TourProvider";
import { useTranslation } from "react-i18next";
import { useExplorersAndConverters } from "../context/ExplorersAndConvertersContext";

export default function ScopeStepConverter({
  supervised,
  targetColumn,
  setTargetColumn,
  tool,
  rows,
  setRows,
  columns,
  setColumns,
  notebook,
  nextStep,
  hideButtons = false,
}) {
  const theme = useTheme();
  const [datasetInfo, setDatasetInfo] = useState(0);
  const tourContext = useTourContext();
  const allowedTypes = tool?.metadata?.allowed_types || [];
  const allowedDtypes = tool?.metadata?.allowed_dtypes || [];
  const nonAllowedDtypes = tool?.metadata?.non_allowed_dtypes || [];
  const inputCardinality = tool?.metadata?.input_cardinality || {};
  const { t } = useTranslation(["common", "datasets"]);
  const { columnTypes } = useExplorersAndConverters();
  const excludedColumnIds = useMemo(
    () => (targetColumn ? [targetColumn.idx - 1] : []),
    [targetColumn],
  );

  const handleSubmit = () => {
    nextStep();
    if (tourContext && tourContext.run) {
      setTimeout(() => {
        tourContext.nextStep();
      }, 500);
    }
  };
  const [isColumnSelectionValid, setIsColumnSelectionValid] = useState(false);

  useEffect(() => {
    let isMounted = true;

    const fetchAllData = async () => {
      try {
        const data = await getDatasetInfoByFilePath(notebook.file_path);
        if (!isMounted) return;
        setDatasetInfo(data);
      } catch (error) {
        console.error("Error fetching dataset info:", error);
      }
    };

    fetchAllData();

    return () => {
      isMounted = false;
    };
  }, [notebook.file_path]);

  return (
    <Box
      sx={{
        display: "flex",
        flexDirection: "column",
        flex: 1,
        height: "100%",
        gap: 2,
        minHeight: 0,
      }}
      data-tour="column-selector-converter-container"
    >
      {/* Content */}
      <Box
        sx={{
          flex: 1,
          minHeight: 0,
          overflowY: "auto",
          display: "flex",
          flexDirection: "column",
          gap: 2,
        }}
      >
        <Typography
          variant="body2"
          sx={{ color: theme.palette.text.primary, mb: 1 }}
        >
          {t("datasets:label.selectScopeDescriptionColumns")}
        </Typography>
        {/* Scope selection UI */}
        <ColumnSelector
          file_path={notebook.file_path}
          tool={tool}
          allowedTypes={allowedTypes}
          allowedDtypes={allowedDtypes}
          nonAllowedDtypes={nonAllowedDtypes}
          excludedColumnIds={excludedColumnIds}
          inputCardinality={inputCardinality}
          columnTypes={columnTypes}
          onSelectionChange={(columnsInfo) => {
            const processedColumns = columnsInfo.map((col) => ({
              idx: col.id + 1,
              columnName: col.columnName,
              valueType: col.valueType,
              dataType: col.dataType,
            }));
            setColumns(processedColumns);
          }}
          onValidationChange={(isValid) => setIsColumnSelectionValid(isValid)}
        />
        <Typography
          variant="body2"
          sx={{ color: theme.palette.text.secondary }}
        >
          {t("datasets:label.selectScopeDescriptionRows")}
        </Typography>
        <RowSelector
          totalRows={datasetInfo?.total_rows || 0}
          initialRows={rows}
          onSelectionChange={(selectedRows) => {
            setRows(selectedRows);
          }}
        />
      </Box>

      {/* Buttons */}
      <Box
        sx={{
          flexShrink: 0,
          display: "flex",
          alignItems: "center",
          gap: 1,
          mt: "auto",
          pt: 2,
          borderTop: 1,
          borderColor: "divider",
        }}
      >
        {supervised && (
          <ConverterClassColumnModal
            updateClassColumn={(column) => {
              const processedColumn = {
                idx: column.id + 1,
                columnName: column.columnName,
                valueType: column.valueType,
                dataType: column.dataType,
              };
              setTargetColumn(processedColumn);
            }}
            classColumnInitialValue={targetColumn?.idx}
            notebook={notebook}
          />
        )}
        {supervised && (
          <Tooltip
            title={t("datasets:label.helpSelectClassColumn")}
            placement="top"
          >
            <IconButton>
              <HelpIcon />
            </IconButton>
          </Tooltip>
        )}

        <Box sx={{ flexGrow: 1 }}>
          <FormSchemaButtonGroup
            onFormSubmit={handleSubmit}
            error={
              !isColumnSelectionValid || (supervised ? !targetColumn : false)
            }
            saveButtonText={
              Object.values(tool.schema.properties).length > 0
                ? t("common:next")
                : t("common:save")
            }
            data-tour="converter-scope-next-button"
            sx={{ borderTop: 0, pt: 0, mt: 0 }}
          />
        </Box>
      </Box>
    </Box>
  );
}
