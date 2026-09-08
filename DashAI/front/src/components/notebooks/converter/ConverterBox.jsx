import React, { useState, useEffect } from "react";
import {
  Paper,
  Box,
  Typography,
  Tooltip,
  CircularProgress,
  IconButton,
} from "@mui/material";
import { useTheme, alpha } from "@mui/material/styles";
import { Delete } from "@mui/icons-material";
import {
  MaterialReactTable,
  useMaterialReactTable,
} from "material-react-table";
import Transform from "@mui/icons-material/Transform";
import RunStatusDot from "../../shared/RunStatusDot";
import { getConverterStatus } from "../../../utils/converterStatus";
import { getComponentById } from "../../../api/component";
import { getConverterById } from "../../../api/converter";
import { useTranslation } from "react-i18next";
import { useTableLocalization } from "../../../utils/useTableLocalization";

function ConverterParametersTable({ converter, t, localization }) {
  const paramColumns = [
    { accessorKey: "key", header: t("common:parameter"), grow: 1 },
    { accessorKey: "value", header: t("common:value"), grow: 4 },
  ];

  const paramRows = [
    {
      key: t("datasets:label.targetColumn"),
      value: converter.parameters.target?.columnName,
    },
    {
      key: t("datasets:label.scopeColumns"),
      value:
        converter.parameters.scope?.columns?.length === 0
          ? "All"
          : converter.parameters.scope.columns
              .map((col) => col.columnName)
              .join(", "),
    },
    {
      key: t("datasets:label.scopeRows"),
      value:
        converter.parameters.scope.rows.length === 0
          ? "All"
          : converter.parameters.scope.rows.join(", "),
    },
  ];

  const table = useMaterialReactTable({
    columns: paramColumns,
    data: paramRows,
    muiTableBodyCellProps: { sx: { whiteSpace: "pre" } },
    localization,
    initialState: { density: "compact" },
    enablePagination: false,
    enableTopToolbar: false,
    enableBottomToolbar: false,
    enableColumnActions: false,
    enableSorting: false,
    enableColumnFilter: false,
    muiTablePaperProps: { elevation: 0 },
  });

  return <MaterialReactTable table={table} />;
}

export default function ConverterBox({
  converter,
  onStatusChange,
  handleConverterDeleteClick,
  isHighlighted = false,
}) {
  const theme = useTheme();
  const [converterComponent, setConverterComponent] = useState({});
  const { t } = useTranslation(["common", "datasets"]);
  const localization = useTableLocalization();

  useEffect(() => {
    const fetchConverterComponent = async () => {
      try {
        const component = await getComponentById(converter.converter);
        setConverterComponent(component);
      } catch (error) {
        console.error("Failed to fetch converter component:", error);
      }
    };

    fetchConverterComponent();
  }, [converter.converter, t]);

  useEffect(() => {
    let intervalId;

    const fetchConverterStatus = async () => {
      try {
        const updatedConverter = await getConverterById(converter.id);

        if (updatedConverter.status !== converter.status) {
          onStatusChange(updatedConverter.id, updatedConverter.status);
        }

        const status = updatedConverter.status;
        if (status === 3 || status === 4) {
          // Finished or Error
          clearInterval(intervalId);
        }
      } catch (error) {
        console.error("Failed to fetch converter status:", error);
        clearInterval(intervalId);
      }
    };

    const currentStatus = converter.status;
    if (currentStatus !== 3 && currentStatus !== 4) {
      //  Not Finished and not Error
      intervalId = setInterval(fetchConverterStatus, 1500);
    }

    return () => clearInterval(intervalId);
  }, [converter.id, converter.status, onStatusChange]);

  const statusLabel = converter.status;

  return (
    <Paper
      key={converter.id}
      variant="outlined"
      className="converter-box"
      sx={{
        p: 4,
        bgcolor: "background.paper",
        borderColor: theme.palette.ui.border,
        borderRadius: 1,
        height: "100%",
        position: "relative",
        zIndex: isHighlighted ? 1 : 0,
        "@keyframes newItemHighlight": {
          "0%": { boxShadow: "none" },
          "20%": {
            boxShadow: `0 0 0 3px ${alpha(theme.palette.primary.main, 0.65)}, 0 0 24px 8px ${alpha(theme.palette.primary.main, 0.2)}`,
          },
          "100%": { boxShadow: "none" },
        },
        animation: isHighlighted
          ? "newItemHighlight 4s ease-in-out forwards"
          : "none",
      }}
    >
      <Box
        sx={{
          display: "flex",
          flexDirection: "column",
          height: "100%",
        }}
      >
        {/* Header */}
        <Box
          sx={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            mb: 4,
          }}
        >
          <Box sx={{ display: "flex", alignItems: "center", gap: 2 }}>
            <Transform
              sx={{ color: theme.palette.primary.main, fontSize: 20 }}
            />
            <Typography variant="h6">
              {converterComponent.display_name}
            </Typography>
            <Tooltip title={getConverterStatus(statusLabel, t)}>
              <span>
                <RunStatusDot
                  status={statusLabel}
                  colorKey={
                    statusLabel !== 3 && statusLabel !== 4 ? "info" : undefined
                  }
                />
              </span>
            </Tooltip>
          </Box>
          <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
            {(statusLabel === 4 || statusLabel === 3) && ( // Error or Finished
              <IconButton
                size="small"
                aria-label="delete"
                color="error"
                onClick={() => handleConverterDeleteClick(converter)}
              >
                <Delete fontSize="small" />
              </IconButton>
            )}
          </Box>
        </Box>

        {statusLabel === 3 ? ( // Finished
          <Box
            sx={{
              flexGrow: 1,
              bgcolor: theme.palette.background.default,
              borderRadius: 1,
              display: "flex",
              flexDirection: "column",
              p: 4,
              overflow: "hidden",
            }}
          >
            {/* Descripción */}
            <Typography variant="body2" sx={{ color: "text.secondary", mb: 4 }}>
              {converterComponent.description}
            </Typography>

            {/* Parámetros en tabla */}
            {converter.parameters && (
              <ConverterParametersTable
                converter={converter}
                t={t}
                localization={localization}
              />
            )}
          </Box>
        ) : statusLabel === 4 ? ( // Error
          <Box
            sx={{
              flexGrow: 1,
              bgcolor: theme.palette.background.default,
              borderRadius: 1,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              p: 2,
            }}
          >
            <Typography
              variant="body2"
              sx={{ color: "error.main", textAlign: "center" }}
            >
              {t("datasets:error.converterFailed")}
            </Typography>
          </Box>
        ) : (
          <Box
            sx={{
              flexGrow: 1,
              bgcolor: theme.palette.ui.hover,
              borderRadius: 1,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            <CircularProgress size={20} sx={{ mr: 2 }} />
            <Typography>{t("common:processing")}</Typography>
          </Box>
        )}
      </Box>
    </Paper>
  );
}
