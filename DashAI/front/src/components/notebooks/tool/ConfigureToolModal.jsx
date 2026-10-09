import { useState, useCallback } from "react";
import {
  Box,
  Typography,
  Dialog,
  IconButton,
  Stepper,
  Step,
  StepLabel,
} from "@mui/material";
import { useTheme } from "@mui/material/styles";
import { Close } from "@mui/icons-material";
import TableChartIcon from "@mui/icons-material/TableChart";
import InfoOutlinedIcon from "@mui/icons-material/InfoOutlined";

import DatasetTable from "../dataset/DatasetTable";
import api from "../../../api/api";
import { getDatasetFile, getDatasetFileFiltered } from "../../../api/datasets";
import { useTranslation } from "react-i18next";
import StepperNavigationFooter from "../../shared/StepperNavigationFooter";
import { useExplorersAndConverters } from "../context/ExplorersAndConvertersContext";
import DocumentComposition from "../documentNotebook/DocumentComposition";
import { isDocumentNotebook } from "../notebookColumns";

export default function ConfigureToolModal({
  tool,
  open,
  handleClose,
  notebook,
  FormSection,
}) {
  const theme = useTheme();
  const { t } = useTranslation(["datasets", "common"]);
  const [step, setStep] = useState(0);
  const [imageOpen, setImageOpen] = useState(false);
  const { columnTypes } = useExplorersAndConverters();

  const fetchDatasetPage = useCallback(
    async (page, pageSize, filterModel, sortModel) => {
      const hasFilters =
        filterModel?.items?.length > 0 || (sortModel && sortModel.length > 0);
      const data = hasFilters
        ? await getDatasetFileFiltered(
            notebook.file_path,
            page,
            pageSize,
            filterModel,
            sortModel,
          )
        : await getDatasetFile(notebook.file_path, page, pageSize);
      return { rows: data.rows ?? [], total: data.total ?? 0 };
    },
    [notebook?.file_path],
  );

  if (!tool) return null;

  const steps =
    Object.values(tool.schema.properties).length > 0
      ? [
          t("datasets:label.configureScope"),
          t("datasets:label.configureParameters"),
        ]
      : [t("datasets:label.configureScope")];

  const totalColumns = Object.keys(columnTypes).length;
  const isDocument = isDocumentNotebook(notebook);

  return (
    <Dialog
      open={open}
      onClose={() => {}}
      slotProps={{
        backdrop: {
          sx: {
            backgroundColor: "rgba(0, 0, 0, 0.7)",
          },
        },
        paper: {
          sx: {
            width: { xs: "95%", md: "1400px" },
            maxWidth: "100%",
            borderRadius: 2,
            height: "90vh",
            display: "flex",
            flexDirection: "column",
            overflow: "hidden",
            bgcolor: theme.palette.background.default,
            backgroundImage: "none",
            border: `1px solid ${theme.palette.ui.borderDark}`,
          },
        },
      }}
    >
      {/* HEADER */}
      <Box
        sx={{
          p: 4,
          borderBottom: "1px solid",
          borderColor: theme.palette.ui.borderDark,
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          gap: 4,
          flexShrink: 0,
        }}
      >
        <Typography variant="h6" fontWeight="600" sx={{ whiteSpace: "nowrap" }}>
          {t("datasets:label.configureToolTitle", {
            toolType: tool.type,
            toolName: tool.display_name,
          })}
        </Typography>

        <Box sx={{ flex: 1 }}>
          <Stepper activeStep={step}>
            {steps.map((label) => (
              <Step key={label} completed={false}>
                <StepLabel>{label}</StepLabel>
              </Step>
            ))}
          </Stepper>
        </Box>

        <IconButton onClick={handleClose}>
          <Close />
        </IconButton>
      </Box>

      {/* SPLIT CONTENT */}
      <Box
        sx={{
          flex: 1,
          display: "flex",
          overflow: "hidden",
          minHeight: 0,
        }}
      >
        {/* LEFT — Configuration form */}
        <Box
          sx={{
            flex: 1,
            display: "flex",
            flexDirection: "column",
            overflow: "hidden",
            p: 4,
            borderRight: "1px solid",
            borderColor: theme.palette.ui.borderDark,
            minWidth: 0,
            minHeight: 0,
          }}
        >
          <FormSection
            step={step}
            setStep={setStep}
            handleClose={handleClose}
            tool={tool}
            notebook={notebook}
          />
        </Box>

        {/* RIGHT — Description + Dataset Preview */}
        <Box
          sx={{
            width: { xs: "100%", md: "450px" },
            flexShrink: 0,
            display: "flex",
            flexDirection: "column",
            overflow: "hidden",
            bgcolor: theme.palette.ui.panelLight,
          }}
        >
          {/* About section */}
          <Box
            sx={{
              p: 4,
              borderBottom: "1px solid",
              borderColor: theme.palette.ui.borderDark,
              overflow: "auto",
              flex: 1,
            }}
          >
            <Box
              sx={{
                display: "flex",
                alignItems: "center",
                gap: 2,
                mb: 3,
              }}
            >
              <InfoOutlinedIcon
                sx={{ fontSize: 20, color: theme.palette.primary.main }}
              />
              <Typography
                variant="subtitle1"
                fontWeight={600}
                sx={{ color: theme.palette.primary.main }}
              >
                {t("datasets:label.aboutTool", {
                  toolName: tool.display_name,
                })}
              </Typography>
            </Box>

            <Typography
              variant="body2"
              sx={{
                color: "text.secondary",
                lineHeight: 1.6,
                mb: 4,
              }}
            >
              {tool.description || t("common:noDescription")}
            </Typography>

            <Box
              onClick={() => setImageOpen(true)}
              sx={{
                cursor: "pointer",
                transition: "opacity 0.2s",
                "&:hover": { opacity: 0.8 },
              }}
            >
              <img
                src={`${api.defaults.baseURL}/v1/component/image/${tool.name}/`}
                alt={tool.display_name}
                style={{
                  width: "100%",
                  height: "auto",
                  maxHeight: "200px",
                  objectFit: "contain",
                  display: "block",
                }}
              />
            </Box>

            {/* Image lightbox */}
            <Dialog
              open={imageOpen}
              onClose={() => setImageOpen(false)}
              maxWidth={false}
              slotProps={{
                backdrop: {
                  sx: { backgroundColor: "rgba(0, 0, 0, 0.85)" },
                },
                paper: {
                  sx: {
                    bgcolor: "transparent",
                    boxShadow: "none",
                    backgroundImage: "none",
                    overflow: "visible",
                  },
                },
              }}
            >
              <Box sx={{ position: "relative" }}>
                <IconButton
                  onClick={() => setImageOpen(false)}
                  sx={{
                    position: "absolute",
                    top: -40,
                    right: -40,
                    color: "white",
                  }}
                >
                  <Close />
                </IconButton>
                <img
                  src={`${api.defaults.baseURL}/v1/component/image/${tool.name}/`}
                  alt={tool.display_name}
                  style={{
                    maxWidth: "90vw",
                    maxHeight: "85vh",
                    objectFit: "contain",
                    display: "block",
                    borderRadius: 8,
                  }}
                />
              </Box>
            </Dialog>
          </Box>

          {/* Dataset Preview section */}
          {isDocument ? (
            <Box sx={{ flex: 1, overflow: "auto", p: 4, minHeight: 0 }}>
              <Box
                sx={{ display: "flex", alignItems: "center", gap: 2, mb: 3 }}
              >
                <TableChartIcon
                  sx={{ fontSize: 20, color: theme.palette.primary.main }}
                />
                <Typography
                  variant="subtitle1"
                  fontWeight={600}
                  sx={{ color: theme.palette.primary.main }}
                >
                  {t("datasets:documentNotebook.documentItems")}
                </Typography>
              </Box>
              <DocumentComposition columnTypes={columnTypes} />
            </Box>
          ) : (
            <Box
              sx={{
                flex: 1,
                display: "flex",
                flexDirection: "column",
                overflow: "hidden",
                p: 4,
                minHeight: 0,
              }}
            >
              <Box
                sx={{
                  display: "flex",
                  alignItems: "center",
                  gap: 2,
                  mb: 2,
                }}
              >
                <TableChartIcon
                  sx={{ fontSize: 20, color: theme.palette.primary.main }}
                />
                <Typography
                  variant="subtitle1"
                  fontWeight={600}
                  sx={{ color: theme.palette.primary.main, flex: 1 }}
                >
                  {t("datasets:label.datasetPreview")}
                </Typography>
                <Typography
                  variant="caption"
                  sx={{ color: "text.secondary", flexShrink: 0 }}
                >
                  {notebook?.name} – {totalColumns} {t("common:columns")}
                </Typography>
              </Box>

              <Box sx={{ flex: 1, overflow: "auto", minHeight: 0 }}>
                <DatasetTable
                  fetchPage={fetchDatasetPage}
                  deps={[notebook?.file_path]}
                  initialPageSize={3}
                  datasetPath={notebook?.file_path}
                  columnTypes={columnTypes}
                  enableTopToolbar={false}
                  enableRowsPerPageSelector={false}
                />
              </Box>
            </Box>
          )}
        </Box>
      </Box>
    </Dialog>
  );
}
