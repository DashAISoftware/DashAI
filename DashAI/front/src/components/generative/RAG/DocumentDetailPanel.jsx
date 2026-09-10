import { useState, useEffect, useRef, useCallback } from "react";
import { useTranslation } from "react-i18next";
import {
  Box,
  Typography,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Button,
  CircularProgress,
  Divider,
  Paper,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions,
  Alert,
  Collapse,
  IconButton,
} from "@mui/material";
import PropTypes from "prop-types";
import { ExpandMore, ExpandLess } from "@mui/icons-material";
import {
  getExtractorOptions,
  extractDocumentText,
  updateDocumentExtractor,
} from "../../../api/rag";
import FormSchema from "../../shared/FormSchema";
import FormSchemaContainer from "../../shared/FormSchemaContainer";
import { resolveDefaults } from "../../../utils/schema";

/**
 * Document detail panel showing document info, extractor selection,
 * content preview, and extractor change flow.
 *
 * The extractor params are rendered through DashAI's schema-driven form
 * (FormSchema), so each extractor shows fields generated from its SCHEMA
 * (e.g. EasyOCRExtractor shows `languages` and `gpu`).
 *
 * @param {object}   props
 * @param {object}   [props.selectedDocument] - The currently selected document, or null.
 * @param {function} [props.onExtractorChanged] - Callback invoked when extractor is saved.
 * @returns {JSX.Element}
 */
export default function DocumentDetailPanel({
  selectedDocument,
  onExtractorChanged,
}) {
  const { t } = useTranslation(["generative", "common"]);
  const [extractors, setExtractors] = useState([]);
  const [selectedExtractor, setSelectedExtractor] = useState("");
  const [params, setParams] = useState({});
  const [content, setContent] = useState("");
  const [contentLoading, setContentLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [affectedSessions, setAffectedSessions] = useState([]);
  const [previewOpen, setPreviewOpen] = useState(false);
  const formikRef = useRef(null);

  // Load extractor options on mount
  useEffect(() => {
    const loadExtractors = async () => {
      try {
        const options = await getExtractorOptions();
        setExtractors(options);
      } catch (e) {
        console.error("Failed to load extractors:", e);
      }
    };
    loadExtractors();
  }, []);

  // Reset when document changes
  useEffect(() => {
    if (selectedDocument) {
      const currentName = selectedDocument.extractor?.component || "";
      const currentParams = selectedDocument.extractor?.params || {};
      setSelectedExtractor(currentName);
      setContent("");
      setError("");
      if (currentName && Object.keys(currentParams).length === 0) {
        resolveDefaults(currentName)
          .then((defaults) => setParams(defaults))
          .catch((err) => {
            console.error(
              `Failed to resolve defaults for ${currentName}:`,
              err,
            );
            setParams({});
          });
      } else {
        setParams(currentParams);
      }
    }
  }, [selectedDocument]);

  /**
   * Build the { component, params } ref to send to the backend, using the
   * latest values from the schema form when available.
   * @returns {{ component: string, params: object }}
   */
  const buildExtractorRef = useCallback(() => {
    const latestParams =
      formikRef.current?.values &&
      Object.keys(formikRef.current.values).length > 0
        ? formikRef.current.values
        : params;
    return { component: selectedExtractor, params: latestParams };
  }, [selectedExtractor, params]);

  /**
   * Handle extractor selection: resolve the schema defaults for the chosen
   * component so the form starts with the right param values.
   * @param {object} e - The select change event.
   */
  const handleExtractorChange = async (e) => {
    const name = e.target.value;
    setSelectedExtractor(name);
    setError("");
    try {
      const defaults = await resolveDefaults(name);
      setParams(defaults);
    } catch (err) {
      console.error(`Failed to resolve defaults for ${name}:`, err);
      setParams({});
    }
  };

  /**
   * Store the latest param values coming from the schema form.
   * @param {object} values - The form parameter values.
   */
  const handleParamsChange = useCallback((values) => {
    setParams(values);
  }, []);

  if (!selectedDocument) {
    return (
      <Box sx={{ p: 3, textAlign: "center", color: "text.secondary" }}>
        <Typography variant="body1">
          {t("generative:ragDocumentsPage.detailPanel.noDocumentSelected")}
        </Typography>
      </Box>
    );
  }

  const docExtractorName = selectedDocument.extractor?.component || "";
  const docExtractorParams = selectedDocument.extractor?.params || {};

  // Filter extractors by file type compatibility
  const compatibleExtractors = extractors.filter((ext) => {
    const supportedTypes = ext.metadata?.supported_file_types || [];
    return (
      supportedTypes.length === 0 ||
      supportedTypes.includes(selectedDocument.file_type)
    );
  });

  const hasChanged =
    !!selectedExtractor &&
    (selectedExtractor !== docExtractorName ||
      JSON.stringify(params) !== JSON.stringify(docExtractorParams));

  const handleProcessDocument = async () => {
    setContentLoading(true);
    setError("");
    setContent("");
    try {
      const ref = buildExtractorRef();
      const result = await extractDocumentText(
        Number(selectedDocument.id),
        ref,
        false, // Preview mode
      );
      setContent(result.text);
      setPreviewOpen(true);
    } catch (e) {
      setError(e.message || "Extraction failed");
    } finally {
      setContentLoading(false);
    }
  };

  const handleSaveExtractor = async () => {
    if (!hasChanged) return;
    setSaving(true);
    setError("");
    try {
      const ref = buildExtractorRef();
      await updateDocumentExtractor(Number(selectedDocument.id), ref, false);
      if (onExtractorChanged) onExtractorChanged();
    } catch (e) {
      const message = e.response?.data?.detail || e.message || "";
      if (e.response?.status === 409) {
        // Need confirmation
        const detail =
          typeof e.response.data.detail === "object"
            ? e.response.data.detail
            : { detail: message, affected_sessions: [] };
        setAffectedSessions(detail.affected_sessions || []);
        setConfirmOpen(true);
      } else {
        setError(message || "Failed to save extractor");
      }
    } finally {
      setSaving(false);
    }
  };

  const handleConfirmForce = async () => {
    setConfirmOpen(false);
    setSaving(true);
    try {
      const ref = buildExtractorRef();
      await updateDocumentExtractor(Number(selectedDocument.id), ref, true);
      if (onExtractorChanged) onExtractorChanged();
    } catch (e) {
      const message = e.response?.data?.detail || e.message || "";
      setError(typeof message === "object" ? JSON.stringify(message) : message);
    } finally {
      setSaving(false);
    }
  };

  return (
    <Box
      sx={{ p: 2, height: "100%", display: "flex", flexDirection: "column" }}
    >
      {/* Document Info */}
      <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
        {t("generative:ragDocumentsPage.detailPanel.documentInfo")}
      </Typography>
      <Box sx={{ mb: 1 }}>
        <Typography variant="body2">
          <strong>{t("generative:ragDocumentsPage.detailPanel.name")}:</strong>{" "}
          {selectedDocument.file_name || selectedDocument.name}
        </Typography>
        <Typography variant="body2">
          <strong>{t("generative:ragDocumentsPage.detailPanel.type")}:</strong>{" "}
          {selectedDocument.file_type}
        </Typography>
      </Box>

      <Divider sx={{ my: 2 }} />

      {/* Extractor Selector */}
      <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
        {t("generative:ragDocumentsPage.detailPanel.extractor")}
      </Typography>
      <FormControl fullWidth size="small" sx={{ mb: 1 }}>
        <InputLabel>
          {t("generative:ragDocumentsPage.detailPanel.extractor")}
        </InputLabel>
        <Select
          value={selectedExtractor}
          label={t("generative:ragDocumentsPage.detailPanel.extractor")}
          onChange={handleExtractorChange}
        >
          {compatibleExtractors.map((ext) => (
            <MenuItem key={ext.name} value={ext.name}>
              {ext.name}
            </MenuItem>
          ))}
        </Select>
      </FormControl>

      {/* Schema-driven extractor params form */}
      <FormSchemaContainer key={`extractor-provider-${selectedExtractor}`}>
        <FormSchema
          key={`extractor-form-${selectedExtractor}`}
          model={selectedExtractor}
          initialValues={params}
          autoSave
          onFormSubmit={handleParamsChange}
          formSubmitRef={formikRef}
          hideButtons
          showBorder={false}
        />
      </FormSchemaContainer>

      {/* Action buttons */}
      <Box sx={{ display: "flex", gap: 1, mb: 2 }}>
        <Button
          variant="outlined"
          size="small"
          onClick={handleProcessDocument}
          disabled={contentLoading}
        >
          {contentLoading ? (
            <CircularProgress size={20} sx={{ mr: 1 }} />
          ) : null}
          {t("generative:ragDocumentsPage.detailPanel.processAndShowContent")}
        </Button>
        {hasChanged && (
          <Button
            variant="contained"
            size="small"
            color="primary"
            onClick={handleSaveExtractor}
            disabled={saving}
          >
            {saving ? <CircularProgress size={20} sx={{ mr: 1 }} /> : null}
            {t("generative:ragDocumentsPage.detailPanel.saveExtractor")}
          </Button>
        )}
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 1 }} onClose={() => setError("")}>
          {error}
        </Alert>
      )}

      <Divider sx={{ my: 1 }} />

      {/* Content Preview */}
      <Box
        sx={{ display: "flex", alignItems: "center", cursor: "pointer" }}
        onClick={() => setPreviewOpen((prev) => !prev)}
      >
        <Typography variant="subtitle1" fontWeight="bold" sx={{ flex: 1 }}>
          {t("generative:ragDocumentsPage.detailPanel.contentPreview")}
        </Typography>
        <IconButton size="small" aria-label="toggle content preview">
          {previewOpen ? <ExpandLess /> : <ExpandMore />}
        </IconButton>
      </Box>
      <Collapse in={previewOpen}>
        {contentLoading && (
          <Box sx={{ textAlign: "center", py: 4 }}>
            <CircularProgress />
            <Typography variant="body2" sx={{ mt: 1 }}>
              {t("generative:ragDocumentsPage.detailPanel.extracting")}
            </Typography>
          </Box>
        )}
        {!contentLoading && !content && (
          <Typography variant="body2" color="text.secondary">
            {t("generative:ragDocumentsPage.detailPanel.noContent")}
          </Typography>
        )}
        {!contentLoading && content && (
          <Paper
            variant="outlined"
            sx={{
              p: 2,
              maxHeight: 400,
              overflow: "auto",
              whiteSpace: "pre-wrap",
              fontSize: "0.85rem",
              flex: 1,
            }}
          >
            {content}
          </Paper>
        )}
      </Collapse>

      {/* Confirmation Dialog */}
      <Dialog open={confirmOpen} onClose={() => setConfirmOpen(false)}>
        <DialogTitle>
          {t(
            "generative:ragDocumentsPage.detailPanel.changeExtractorConfirmTitle",
          )}
        </DialogTitle>
        <DialogContent>
          <DialogContentText>
            {t(
              "generative:ragDocumentsPage.detailPanel.changeExtractorConfirmBody",
              {
                count: affectedSessions.length,
              },
            )}
          </DialogContentText>
          {affectedSessions.length > 0 && (
            <Box sx={{ mt: 1 }}>
              {affectedSessions.map((s) => (
                <Typography key={s.id} variant="body2">
                  • {s.name} (ID: {s.id})
                </Typography>
              ))}
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setConfirmOpen(false)}>
            {t("common:cancel")}
          </Button>
          <Button
            onClick={handleConfirmForce}
            color="warning"
            variant="contained"
          >
            {t("generative:ragDocumentsPage.detailPanel.saveExtractor")}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}

DocumentDetailPanel.propTypes = {
  selectedDocument: PropTypes.shape({
    id: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
    file_name: PropTypes.string,
    file_type: PropTypes.string,
    name: PropTypes.string,
    extractor: PropTypes.shape({
      component: PropTypes.string,
      params: PropTypes.object,
    }),
    default_extractor: PropTypes.shape({
      component: PropTypes.string,
      params: PropTypes.object,
    }),
  }),
  onExtractorChanged: PropTypes.func,
};
