import { useCallback, useEffect, useRef, useState } from "react";
import PropTypes from "prop-types";
import {
  Alert,
  Box,
  Button,
  CircularProgress,
  Grid,
  Tab,
  Typography,
} from "@mui/material";
import { useTheme } from "@mui/material/styles";
import { AddCircleOutline as AddIcon } from "@mui/icons-material";
import { useTranslation } from "react-i18next";
import PillTabs from "../shared/PillTabs";
import DocumentRightBar from "./DocumentRightBar";
import DocumentHeader from "./DocumentHeader";
import DocumentRenderer from "./DocumentRenderer";
import DocumentImageGrid from "./DocumentImageGrid";
import { scrollToPosition } from "./documentKinds";
import { getDocumentContent, getDocumentOutline } from "../../api/documents";
import { DOCUMENT_STATUS } from "../../hooks/datasets/useDocuments";
import { formatDate } from "../../pages/results/constants/formatDate";
import { useDatasetsAndNotebooks } from "../custom/contexts/DatasetsAndNotebooksContext";

const PAGE_SIZE = 100;
const VIEWS = ["document", "structure", "images"];
const JUMP_LOOKAHEAD = 25;

function usePagedContent(documentId, contentType, enabled) {
  const [items, setItems] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [failed, setFailed] = useState(false);
  const startedRef = useRef(false);
  const itemsRef = useRef([]);
  const totalRef = useRef(Infinity);

  const append = useCallback((page) => {
    if (page.offset !== itemsRef.current.length) return;
    itemsRef.current = [...itemsRef.current, ...page.items];
    totalRef.current = page.total;
    setItems(itemsRef.current);
    setTotal(page.total);
  }, []);

  const loadMore = useCallback(async () => {
    setLoading(true);
    setFailed(false);
    try {
      append(
        await getDocumentContent(
          documentId,
          contentType,
          itemsRef.current.length,
          PAGE_SIZE,
        ),
      );
    } catch (error) {
      setFailed(true);
    } finally {
      setLoading(false);
    }
  }, [documentId, contentType, append]);

  const loadThrough = useCallback(
    async (position) => {
      try {
        while (
          itemsRef.current.length < totalRef.current &&
          (itemsRef.current.length === 0 ||
            itemsRef.current[itemsRef.current.length - 1].position < position)
        ) {
          append(
            await getDocumentContent(
              documentId,
              contentType,
              itemsRef.current.length,
              PAGE_SIZE,
            ),
          );
        }
      } catch (error) {
        setFailed(true);
      }
    },
    [documentId, contentType, append],
  );

  useEffect(() => {
    if (!enabled || startedRef.current) return;
    startedRef.current = true;
    loadMore();
  }, [enabled, loadMore]);

  return { items, total, loading, failed, loadMore, loadThrough };
}

function LoadMoreFooter({ content }) {
  const { t } = useTranslation(["datasets"]);
  return (
    <Box sx={{ display: "flex", justifyContent: "center", mt: 3 }}>
      {content.loading && <CircularProgress size={24} />}
      {!content.loading && content.items.length < content.total && (
        <Button variant="outlined" onClick={content.loadMore}>
          {t("datasets:document.loadMore")}
        </Button>
      )}
    </Box>
  );
}

LoadMoreFooter.propTypes = { content: PropTypes.object.isRequired };

export default function DocumentView({ dataDocument }) {
  const { t } = useTranslation(["datasets", "common"]);
  const theme = useTheme();
  const { setRightBarContent } = useDatasetsAndNotebooks();
  const [tab, setTab] = useState(0);
  const [outline, setOutline] = useState(null);
  const [pendingJump, setPendingJump] = useState(null);
  const documentId = dataDocument?.id;
  const isFinished = dataDocument?.status === DOCUMENT_STATUS.FINISHED;
  const isError = dataDocument?.status === DOCUMENT_STATUS.ERROR;
  const counts = dataDocument?.content_counts || {};
  const view = VIEWS[tab];

  const content = usePagedContent(documentId, "all", isFinished);
  const images = usePagedContent(
    documentId,
    "Image",
    isFinished && view === "images",
  );
  const { loadThrough } = content;

  useEffect(() => {
    if (!isFinished) return undefined;
    let cancelled = false;
    getDocumentOutline(documentId)
      .then((body) => {
        if (!cancelled) setOutline(body.items);
      })
      .catch(() => {
        if (!cancelled) setOutline([]);
      });
    return () => {
      cancelled = true;
    };
  }, [documentId, isFinished]);

  const jumpTo = useCallback(
    async (position) => {
      setTab((current) => (VIEWS[current] === "images" ? 0 : current));
      await loadThrough(position);
      setPendingJump(position);
    },
    [loadThrough],
  );

  useEffect(() => {
    if (pendingJump === null) return undefined;
    const frame = requestAnimationFrame(() => {
      for (let p = pendingJump; p < pendingJump + JUMP_LOOKAHEAD; p += 1) {
        if (scrollToPosition(p, theme.palette.primary.main)) break;
      }
      setPendingJump(null);
    });
    return () => cancelAnimationFrame(frame);
  }, [pendingJump, content.items, tab, theme]);

  useEffect(() => {
    setRightBarContent(<DocumentRightBar outline={outline} onJump={jumpTo} />);
  }, [setRightBarContent, outline, jumpTo]);

  useEffect(() => () => setRightBarContent(null), [setRightBarContent]);

  if (!dataDocument) {
    return (
      <Box sx={{ display: "flex", justifyContent: "center", pt: 8 }}>
        <CircularProgress />
      </Box>
    );
  }

  const active = view === "images" ? images : content;

  return (
    <Box
      sx={{ display: "flex", flexDirection: "column", gap: 2, mt: 4, mx: 2 }}
    >
      <Box sx={{ display: "flex", flexDirection: "column", gap: 4 }}>
        {(isFinished || isError) && (
          <Box
            sx={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              flexWrap: "wrap",
              minHeight: "45px",
            }}
          >
            <Box sx={{ display: "flex", flexDirection: "column", gap: 1 }}>
              <Typography variant="h4">{dataDocument.name}</Typography>
            </Box>
          </Box>
        )}

        {(isFinished || isError) && (
          <Box
            sx={{
              display: "flex",
              justifyContent: "space-between",
              mb: 2,
              flexWrap: "wrap",
            }}
          >
            <Box
              sx={{
                display: "flex",
                flexDirection: "column",
                justifyContent: "center",
              }}
            >
              <Typography variant="subtitle1" color="text.secondary">
                {[
                  formatDate(dataDocument.created),
                  dataDocument.file_name,
                  dataDocument.dataloader,
                ]
                  .filter(Boolean)
                  .join(" | ")}
              </Typography>
            </Box>

            <Box
              sx={{
                display: "flex",
                alignItems: "flex-end",
                gap: 4,
                flexDirection: "column",
              }}
            >
              <Grid
                sx={{
                  minHeight: "40px",
                  display: "flex",
                  gap: 4,
                  flexWrap: "wrap",
                  justifyContent: "flex-start",
                }}
              >
                <Button
                  variant="contained"
                  endIcon={<AddIcon />}
                  disabled
                  sx={{ height: "40px" }}
                >
                  {t("datasets:button.newNotebook")}
                </Button>
              </Grid>
            </Box>
          </Box>
        )}

        {isError && (
          <Alert severity="error">{t("datasets:document.errorMessage")}</Alert>
        )}

        {!isFinished && !isError && (
          <Box
            sx={{
              display: "flex",
              justifyContent: "center",
              alignItems: "center",
              minHeight: 200,
              flexDirection: "column",
              gap: 4,
            }}
          >
            <CircularProgress color="primary" />
            <Typography>{t("datasets:document.processingTitle")}</Typography>
            <Typography
              variant="body2"
              color="text.secondary"
              textAlign="center"
            >
              {t("datasets:document.processingMessage")}
            </Typography>
          </Box>
        )}

        {isFinished && (
          <>
            <DocumentHeader
              totalPages={dataDocument.total_pages}
              textCount={counts.Text}
              imageCount={counts.Image}
            />

            <PillTabs
              minHeight="48px"
              value={tab}
              onChange={(_, value) => setTab(value)}
            >
              <Tab label={t("datasets:document.viewDocument")} />
              <Tab label={t("datasets:document.viewStructure")} />
              <Tab
                label={t("datasets:document.tabImage", {
                  total: counts.Image ?? 0,
                })}
                disabled={!counts.Image}
              />
            </PillTabs>

            <Box sx={{ mb: 4 }}>
              {active.failed && (
                <Alert severity="error" sx={{ mb: 2 }}>
                  {t("datasets:document.loadingFailed")}
                </Alert>
              )}

              {!active.loading &&
                !active.failed &&
                active.items.length === 0 && (
                  <Typography variant="body2" color="text.secondary">
                    {t("datasets:document.noContent")}
                  </Typography>
                )}

              {view === "document" && content.items.length > 0 && (
                <Box
                  sx={{
                    bgcolor: "background.box",
                    borderRadius: 1,
                    p: { xs: 2, md: 4 },
                  }}
                >
                  <DocumentRenderer items={content.items} mode="read" />
                </Box>
              )}

              {view === "structure" && content.items.length > 0 && (
                <DocumentRenderer items={content.items} mode="structure" />
              )}

              {view === "images" && images.items.length > 0 && (
                <DocumentImageGrid images={images.items} onOpen={jumpTo} />
              )}

              <LoadMoreFooter content={active} />
            </Box>
          </>
        )}
      </Box>
    </Box>
  );
}

DocumentView.propTypes = { dataDocument: PropTypes.object };
