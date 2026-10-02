import { useCallback, useEffect, useState } from "react";
import PropTypes from "prop-types";
import {
  Alert,
  Box,
  Button,
  Chip,
  CircularProgress,
  Paper,
  Stack,
  Tab,
  Typography,
} from "@mui/material";
import { useTranslation } from "react-i18next";
import PillTabs from "../shared/PillTabs";
import DataBreadcrumbs from "../notebooks/DataBreadcrumbs";
import DocumentDetailsBar from "./DocumentDetailsBar";
import {
  getDocumentContent,
  getDocumentSourceViewUrl,
} from "../../api/documents";
import { DOCUMENT_STATUS } from "../../hooks/datasets/useDocuments";
import { normalizeUrl } from "../../utils/urlUtils";
import { useDatasetsAndNotebooks } from "../custom/contexts/DatasetsAndNotebooksContext";

const PAGE_SIZE = 50;
const CONTENT_TABS = ["all", "Text", "Image"];

function SourcePreview({ dataDocument }) {
  const { t } = useTranslation(["datasets"]);
  const [text, setText] = useState("");
  const [loading, setLoading] = useState(false);
  const isPdf = dataDocument.file_type === "pdf";
  const sourceUrl = normalizeUrl(getDocumentSourceViewUrl(dataDocument.id));

  useEffect(() => {
    if (isPdf) return undefined;
    let cancelled = false;
    setLoading(true);
    fetch(sourceUrl)
      .then((response) => {
        if (!response.ok) throw new Error(String(response.status));
        return response.text();
      })
      .then((value) => {
        if (!cancelled) setText(value);
      })
      .catch(() => {
        if (!cancelled) setText(t("datasets:document.noPreview"));
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [isPdf, sourceUrl, t]);

  if (isPdf) {
    return (
      <Box
        component="iframe"
        src={sourceUrl}
        title={dataDocument.file_name || dataDocument.name}
        sx={{
          width: "100%",
          height: "100%",
          minHeight: 600,
          border: 1,
          borderColor: "divider",
          borderRadius: 1,
        }}
      />
    );
  }
  return (
    <Paper
      variant="outlined"
      sx={{
        p: 2,
        height: "100%",
        minHeight: 600,
        overflow: "auto",
        whiteSpace: "pre-wrap",
        fontSize: "0.85rem",
      }}
    >
      {loading ? <CircularProgress size={24} /> : text}
    </Paper>
  );
}

SourcePreview.propTypes = { dataDocument: PropTypes.object.isRequired };

function ContentItem({ item }) {
  const { t } = useTranslation(["datasets"]);
  const isImage = item.type === "Image";
  return (
    <Paper variant="outlined" sx={{ p: 2 }}>
      <Stack direction="row" spacing={1} sx={{ mb: 1 }}>
        <Chip
          size="small"
          label={
            isImage
              ? t("datasets:document.imageChip")
              : t("datasets:document.textChip")
          }
        />
        {item.page !== null && item.page !== undefined && (
          <Chip
            size="small"
            variant="outlined"
            label={t("datasets:document.pageLabel", { page: item.page })}
          />
        )}
        <Chip
          size="small"
          variant="outlined"
          label={t("datasets:document.positionLabel", {
            position: item.position + 1,
          })}
        />
      </Stack>
      {isImage ? (
        <Box
          component="img"
          src={normalizeUrl(item.url)}
          alt={t("datasets:document.imageAlt", { position: item.position + 1 })}
          sx={{ maxWidth: "100%", display: "block" }}
        />
      ) : (
        <Typography variant="body2" sx={{ whiteSpace: "pre-wrap" }}>
          {item.content}
        </Typography>
      )}
    </Paper>
  );
}

ContentItem.propTypes = { item: PropTypes.object.isRequired };

export default function DocumentView({ dataDocument }) {
  const { t } = useTranslation(["datasets", "common"]);
  const { setRightBarContent } = useDatasetsAndNotebooks();
  const [tab, setTab] = useState(0);
  const [items, setItems] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [failed, setFailed] = useState(false);
  const documentId = dataDocument?.id;
  const isFinished = dataDocument?.status === DOCUMENT_STATUS.FINISHED;
  const isError = dataDocument?.status === DOCUMENT_STATUS.ERROR;
  const counts = dataDocument?.content_counts || {};
  const contentType = CONTENT_TABS[tab];

  useEffect(() => {
    if (!dataDocument) return undefined;
    setRightBarContent(<DocumentDetailsBar dataDocument={dataDocument} />);
    return () => setRightBarContent(null);
  }, [dataDocument, setRightBarContent]);

  const loadPage = useCallback(
    async (offset) => {
      setLoading(true);
      setFailed(false);
      try {
        const page = await getDocumentContent(
          documentId,
          contentType,
          offset,
          PAGE_SIZE,
        );
        setItems((prev) =>
          offset === 0 ? page.items : [...prev, ...page.items],
        );
        setTotal(page.total);
      } catch (error) {
        setFailed(true);
      } finally {
        setLoading(false);
      }
    },
    [documentId, contentType],
  );

  useEffect(() => {
    if (!isFinished) {
      setItems([]);
      setTotal(0);
      return;
    }
    loadPage(0);
  }, [isFinished, loadPage]);

  if (!dataDocument) {
    return (
      <Box sx={{ display: "flex", justifyContent: "center", pt: 8 }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box
      sx={{
        display: "flex",
        flexDirection: "column",
        width: "100%",
        height: "100%",
        overflow: "auto",
        px: 4,
        pt: 4,
        pb: 4,
      }}
    >
      <DataBreadcrumbs />
      <Typography variant="h5" component="h1" sx={{ mb: 1 }}>
        {dataDocument.name}
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        {[dataDocument.file_name, dataDocument.dataloader]
          .filter(Boolean)
          .join(" | ")}
      </Typography>

      {isError && (
        <Alert severity="error">{t("datasets:document.errorMessage")}</Alert>
      )}
      {!isFinished && !isError && (
        <Alert severity="info" icon={<CircularProgress size={18} />}>
          {t("datasets:document.processingMessage")}
        </Alert>
      )}

      {isFinished && (
        <Box
          sx={{
            display: "flex",
            gap: 3,
            flex: 1,
            minHeight: 0,
            flexWrap: "wrap",
          }}
        >
          <Box
            sx={{
              flex: "1 1 45%",
              minWidth: 320,
              display: "flex",
              flexDirection: "column",
            }}
          >
            <Typography variant="subtitle2" sx={{ mb: 1 }}>
              {t("datasets:document.originalFile")}
            </Typography>
            <SourcePreview dataDocument={dataDocument} />
          </Box>
          <Box
            sx={{
              flex: "1 1 45%",
              minWidth: 320,
              display: "flex",
              flexDirection: "column",
            }}
          >
            <Typography variant="subtitle2" sx={{ mb: 1 }}>
              {t("datasets:document.parsedContent")}
            </Typography>
            <PillTabs
              minHeight="40px"
              value={tab}
              onChange={(_, value) => setTab(value)}
              sx={{ mb: 2 }}
            >
              <Tab label={t("datasets:document.tabAll")} />
              <Tab
                label={t("datasets:document.tabText", {
                  total: counts.Text ?? 0,
                })}
                disabled={!counts.Text}
              />
              <Tab
                label={t("datasets:document.tabImage", {
                  total: counts.Image ?? 0,
                })}
                disabled={!counts.Image}
              />
            </PillTabs>
            {failed && (
              <Alert severity="error" sx={{ mb: 2 }}>
                {t("datasets:document.loadingFailed")}
              </Alert>
            )}
            <Stack
              spacing={2}
              sx={{ overflowY: "auto", flex: 1, minHeight: 0 }}
            >
              {items.map((item) => (
                <ContentItem key={item.position} item={item} />
              ))}
              {!loading && !failed && items.length === 0 && (
                <Typography variant="body2" color="text.secondary">
                  {t("datasets:document.noContent")}
                </Typography>
              )}
              {loading && <CircularProgress size={24} />}
              {!loading && items.length < total && (
                <Button
                  variant="outlined"
                  onClick={() => loadPage(items.length)}
                >
                  {t("datasets:document.loadMore")}
                </Button>
              )}
            </Stack>
          </Box>
        </Box>
      )}
    </Box>
  );
}

DocumentView.propTypes = { dataDocument: PropTypes.object };
