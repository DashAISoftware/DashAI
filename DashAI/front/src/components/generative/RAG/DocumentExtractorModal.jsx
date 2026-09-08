import { useCallback, useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { useTranslation } from "react-i18next";
import {
  Alert,
  Box,
  Button,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogContentText,
  DialogTitle,
  FormControl,
  IconButton,
  InputLabel,
  MenuItem,
  Paper,
  Select,
  Tooltip,
  Typography,
} from "@mui/material";
import PropTypes from "prop-types";
import SettingsIcon from "@mui/icons-material/Settings";
import PlayArrowIcon from "@mui/icons-material/PlayArrow";
import {
  extractDocumentText,
  getExtractorOptions,
  updateDocumentExtractor,
} from "../../../api/rag";
import FormSchema from "../../shared/FormSchema";
import FormSchemaContainer from "../../shared/FormSchemaContainer";
import { resolveDefaults } from "../../../utils/schema";
import { normalizeUrl } from "../../../utils/urlUtils";

/**
 * Modal for inspecting and configuring a document's text extractor.
 *
 * Shows a split view with the original file on the left and the extracted text
 * on the right. The extractor selector sits next to the explanation; a
 * "Settings" button opens a separate dialog with the schema-driven params form.
 */
export default function DocumentExtractorModal({
  open,
  onClose,
  document,
  onExtractorChanged,
}) {
  const { t } = useTranslation(["generative", "common"]);
  const [extractors, setExtractors] = useState([]);
  const [selectedExtractor, setSelectedExtractor] = useState("");
  const [params, setParams] = useState({});
  const [content, setContent] = useState("");
  const [rawContent, setRawContent] = useState("");
  const [rawContentLoading, setRawContentLoading] = useState(false);
  const [contentLoading, setContentLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [affectedSessions, setAffectedSessions] = useState([]);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const formikRef = useRef(null);

  const fileName = document?.file_name || document?.name || "";
  const fileType = document?.file_type || document?.type || "";
  const docExtractorName = document?.extractor?.component || "";
  const docExtractorParams = document?.extractor?.params || {};
  const previewUrl = document?.preview || document?.preview_url;

  const hasChanged =
    !!selectedExtractor &&
    (selectedExtractor !== docExtractorName ||
      JSON.stringify(params) !== JSON.stringify(docExtractorParams));

  /** Filter extractors by file-type compatibility. */
  const compatibleExtractors = extractors.filter((ext) => {
    const supportedTypes = ext.metadata?.supported_file_types || [];
    return supportedTypes.length === 0 || supportedTypes.includes(fileType);
  });

  // --- Extraction ----------------------------------------------------------

  const performExtract = useCallback(async (docId, ref) => {
    setContentLoading(true);
    setContent("");
    setError("");
    try {
      const result = await extractDocumentText(Number(docId), ref, false); // Preview mode
      setContent(result.text);
    } catch (e) {
      setError(e.message || "Extraction failed");
    } finally {
      setContentLoading(false);
    }
  }, []);

  // --- Init on open --------------------------------------------------------

  useEffect(() => {
    if (!open || !document) return;
    setError("");
    setContent("");
    setRawContent("");
    setConfirmOpen(false);
    setSettingsOpen(false);

    const currentName = document.extractor?.component || "";
    const currentParams = document.extractor?.params || {};

    const init = async () => {
      try {
        const options = await getExtractorOptions();
        setExtractors(options);

        const compatible = options.filter((ext) => {
          const supportedTypes = ext.metadata?.supported_file_types || [];
          return (
            supportedTypes.length === 0 || supportedTypes.includes(fileType)
          );
        });

        const initialName = compatible.some((ext) => ext.name === currentName)
          ? currentName
          : compatible[0]?.name || "";
        setSelectedExtractor(initialName);

        let initialParams = currentParams;
        if (initialName && initialName === currentName) {
          if (Object.keys(currentParams).length === 0) {
            try {
              initialParams = await resolveDefaults(initialName);
            } catch {
              initialParams = {};
            }
          }
        } else if (initialName) {
          try {
            initialParams = await resolveDefaults(initialName);
          } catch {
            initialParams = {};
          }
        }
        setParams(initialParams);

        if (initialName) {
          setParams(initialParams);
        }
      } catch (e) {
        setError(e.message || "Failed to load extractor options");
      }
    };
    init();
  }, [open, document, fileType, performExtract]);

  // --- Raw content for non-PDF files ---------------------------------------

  useEffect(() => {
    if (!open || !document) return;
    if (fileType === "pdf" || !previewUrl) {
      setRawContentLoading(false);
      setRawContent("");
      return;
    }
    let cancelled = false;
    setRawContentLoading(true);
    fetch(normalizeUrl(previewUrl))
      .then((res) => res.text())
      .then((text) => {
        if (!cancelled) setRawContent(text);
      })
      .catch(() => {
        if (!cancelled) setRawContent("Error loading file content");
      })
      .finally(() => {
        if (!cancelled) setRawContentLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [open, document, fileType, previewUrl]);

  // --- Extractor change → re-extract ---------------------------------------

  const handleExtractorChange = async (e) => {
    const name = e.target.value;
    setSelectedExtractor(name);
    setError("");
    setContent("");
    let defaults = {};
    try {
      defaults = await resolveDefaults(name);
    } catch (err) {
      console.error(`Failed to resolve defaults for ${name}:`, err);
    }
    setParams(defaults);
  };

  // --- Params form callbacks -----------------------------------------------

  const handleParamsChange = useCallback((values) => {
    setParams(values);
  }, []);

  const buildExtractorRef = useCallback(() => {
    const latestParams =
      formikRef.current?.values &&
      Object.keys(formikRef.current.values).length > 0
        ? formikRef.current.values
        : params;
    return { component: selectedExtractor, params: latestParams };
  }, [selectedExtractor, params]);

  // --- Save ----------------------------------------------------------------

  const handleSaveExtractor = async () => {
    if (!hasChanged) return;
    setSaving(true);
    setError("");
    try {
      const ref = buildExtractorRef();
      const updated = await updateDocumentExtractor(
        Number(document.id),
        ref,
        false,
      );
      if (onExtractorChanged) onExtractorChanged(updated);
    } catch (e) {
      const message = e.response?.data?.detail || e.message || "";
      if (e.response?.status === 409) {
        const detail =
          typeof e.response.data.detail === "object"
            ? e.response.data.detail
            : { detail: message, affected_sessions: [] };
        setAffectedSessions(detail.affected_sessions || []);
        setConfirmOpen(true);
      } else {
        setError(
          typeof message === "object" ? JSON.stringify(message) : message,
        );
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
      const updated = await updateDocumentExtractor(
        Number(document.id),
        ref,
        true,
      );
      if (onExtractorChanged) onExtractorChanged(updated);
    } catch (e) {
      const message = e.response?.data?.detail || e.message || "";
      setError(typeof message === "object" ? JSON.stringify(message) : message);
    } finally {
      setSaving(false);
    }
  };

  // --- Render --------------------------------------------------------------

  const dialogContent = (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="lg"
      fullWidth
      slotProps={{ backdrop: { sx: { backgroundColor: "rgba(0,0,0,0.7)" } } }}
    >
      {/* ── Title bar: file name ── */}
      <Box
        sx={{
          px: 3,
          pt: 2,
          pb: 1,
          borderBottom: 1,
          borderColor: "divider",
        }}
      >
        <Typography variant="h6" align="center" noWrap>
          {fileName}
        </Typography>
      </Box>

      <DialogContent sx={{ pt: 2 }}>
        {!document ? (
          <Typography variant="body1" color="text.secondary">
            {t("common:na")}
          </Typography>
        ) : (
          <Box>
            {/* ── Row 2: explanation (full width) ── */}
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              {t("generative:rag.documents.extractorModal.explanation")}
            </Typography>

            {/* ── Row 3: file preview (left) + extractor config & extracted text (right) ── */}
            <Box
              sx={{
                display: "flex",
                gap: 2,
                flexWrap: "wrap",
              }}
            >
              {/* Left: original file */}
              <Box sx={{ flex: "1 1 48%", minWidth: 300 }}>
                {/* Spacer to align with right column's selector row */}
                <Box sx={{ height: 44, mb: 1 }} />
                <Typography variant="subtitle2" fontWeight="bold" gutterBottom>
                  {t("generative:rag.documents.extractorModal.rawContentLabel")}
                </Typography>
                {fileType === "pdf" && previewUrl ? (
                  <iframe
                    src={normalizeUrl(previewUrl)}
                    title={t(
                      "generative:rag.documents.extractorModal.rawContentLabel",
                    )}
                    width="100%"
                    height="500"
                    style={{ border: "1px solid", borderColor: "divider" }}
                  />
                ) : fileType === "pdf" ? (
                  <Paper
                    variant="outlined"
                    sx={{
                      p: 2,
                      height: 500,
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                    }}
                  >
                    <Typography variant="body2" color="text.secondary">
                      {t("common:na")}
                    </Typography>
                  </Paper>
                ) : (
                  <Paper
                    variant="outlined"
                    sx={{
                      p: 2,
                      height: 500,
                      overflow: "auto",
                      whiteSpace: "pre-wrap",
                      fontSize: "0.85rem",
                    }}
                  >
                    {rawContentLoading ? (
                      <Box sx={{ textAlign: "center", py: 4 }}>
                        <CircularProgress size={28} />
                      </Box>
                    ) : rawContent ? (
                      rawContent
                    ) : (
                      <Typography variant="body2" color="text.secondary">
                        {t("common:na")}
                      </Typography>
                    )}
                  </Paper>
                )}
              </Box>

              {/* Right: extractor selector + extracted text */}
              <Box sx={{ flex: "1 1 48%", minWidth: 300 }}>
                {/* Extractor selector + settings (top-left inside column) */}
                <Box
                  sx={{
                    display: "flex",
                    alignItems: "center",
                    gap: 1,
                    mb: 1,
                  }}
                >
                  <FormControl size="small" sx={{ minWidth: 160 }}>
                    <InputLabel>
                      {t(
                        "generative:rag.documents.extractorModal.extractorLabel",
                      )}
                    </InputLabel>
                    <Select
                      value={selectedExtractor}
                      label={t(
                        "generative:rag.documents.extractorModal.extractorLabel",
                      )}
                      onChange={handleExtractorChange}
                    >
                      {compatibleExtractors.map((ext) => (
                        <MenuItem key={ext.name} value={ext.name}>
                          {ext.name}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                  <Tooltip
                    title={t(
                      "generative:rag.documents.table.configureExtractor",
                    )}
                  >
                    <IconButton
                      size="small"
                      onClick={() => setSettingsOpen(true)}
                      disabled={!selectedExtractor}
                    >
                      <SettingsIcon fontSize="small" />
                    </IconButton>
                  </Tooltip>
                </Box>

                <Typography variant="subtitle2" fontWeight="bold" gutterBottom>
                  {t(
                    "generative:rag.documents.extractorModal.extractedContentLabel",
                  )}
                </Typography>
                <Paper
                  variant="outlined"
                  sx={{
                    p: 2,
                    height: 500,
                    overflow: "auto",
                    whiteSpace: "pre-wrap",
                    fontSize: "0.85rem",
                  }}
                >
                  {contentLoading ? (
                    <Box sx={{ textAlign: "center", py: 4 }}>
                      <CircularProgress />
                      <Typography variant="body2" sx={{ mt: 1 }}>
                        {t(
                          "generative:rag.documents.extractorModal.extracting",
                        )}
                      </Typography>
                    </Box>
                  ) : content ? (
                    content
                  ) : (
                    <Box
                      sx={{
                        display: "flex",
                        flexDirection: "column",
                        alignItems: "center",
                        justifyContent: "center",
                        height: "100%",
                        gap: 1,
                      }}
                    >
                      <Typography variant="body2" color="text.secondary">
                        {t("generative:rag.documents.extractorModal.noContent")}
                      </Typography>
                      <Button
                        variant="contained"
                        size="medium"
                        startIcon={<PlayArrowIcon />}
                        onClick={() => {
                          if (!document || !selectedExtractor) return;
                          performExtract(document.id, buildExtractorRef());
                        }}
                        disabled={!selectedExtractor}
                      >
                        {t(
                          "generative:rag.documents.extractorModal.extractText",
                        )}
                      </Button>
                    </Box>
                  )}
                </Paper>
              </Box>
            </Box>

            {error && (
              <Alert
                severity="error"
                onClose={() => setError("")}
                sx={{ mt: 2 }}
              >
                {error}
              </Alert>
            )}
          </Box>
        )}
      </DialogContent>

      <DialogActions>
        <Button onClick={onClose} disabled={saving}>
          {t("generative:rag.documents.extractorModal.close")}
        </Button>
        {hasChanged ? (
          <Button
            variant="contained"
            color="primary"
            onClick={handleSaveExtractor}
            disabled={saving}
          >
            {saving ? <CircularProgress size={20} sx={{ mr: 1 }} /> : null}
            {t("generative:rag.documents.extractorModal.saveExtractor")}
          </Button>
        ) : (
          <Button variant="contained" color="primary" onClick={onClose}>
            {t("generative:rag.documents.extractorModal.upToDate")}
          </Button>
        )}
      </DialogActions>

      {/* ── Settings dialog: extractor parameters ── */}
      <Dialog
        open={settingsOpen}
        onClose={() => setSettingsOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>
          {selectedExtractor
            ? `${t("generative:rag.documents.extractorModal.extractorLabel")}: ${selectedExtractor}`
            : t("generative:rag.documents.table.configureExtractor")}
        </DialogTitle>
        <DialogContent>
          {selectedExtractor ? (
            <FormSchemaContainer key={`settings-provider-${selectedExtractor}`}>
              <FormSchema
                key={`settings-form-${selectedExtractor}`}
                model={selectedExtractor}
                initialValues={params}
                autoSave
                onFormSubmit={handleParamsChange}
                formSubmitRef={formikRef}
                hideButtons
                showBorder={false}
              />
            </FormSchemaContainer>
          ) : (
            <Typography variant="body2" color="text.secondary">
              {t("generative:rag.documents.extractorModal.noContent")}
            </Typography>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setSettingsOpen(false)}>
            {t("common:close")}
          </Button>
        </DialogActions>
      </Dialog>

      {/* ── Force-conflict confirmation dialog ── */}
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
              { count: affectedSessions.length },
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
            disabled={saving}
          >
            {t("generative:ragDocumentsPage.detailPanel.saveExtractor")}
          </Button>
        </DialogActions>
      </Dialog>
    </Dialog>
  );

  return createPortal(dialogContent, globalThis.document.body);
}

DocumentExtractorModal.propTypes = {
  open: PropTypes.bool.isRequired,
  onClose: PropTypes.func.isRequired,
  document: PropTypes.shape({
    id: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
    file_name: PropTypes.string,
    file_type: PropTypes.string,
    name: PropTypes.string,
    preview: PropTypes.string,
    preview_url: PropTypes.string,
    extractor: PropTypes.shape({
      component: PropTypes.string,
      params: PropTypes.object,
    }),
  }),
  onExtractorChanged: PropTypes.func,
};
