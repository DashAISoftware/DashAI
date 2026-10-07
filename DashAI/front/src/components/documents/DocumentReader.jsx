import { useCallback, useEffect, useRef, useState } from "react";
import PropTypes from "prop-types";
import {
  Alert,
  Box,
  Button,
  CircularProgress,
  Tab,
  Typography,
} from "@mui/material";
import { useTheme } from "@mui/material/styles";
import { useTranslation } from "react-i18next";
import PillTabs from "../shared/PillTabs";
import DocumentRightBar from "./DocumentRightBar";
import DocumentHeader from "./DocumentHeader";
import DocumentRenderer from "./DocumentRenderer";
import DocumentImageGrid from "./DocumentImageGrid";
import { scrollToPosition } from "./documentKinds";
import { useDatasetsAndNotebooks } from "../custom/contexts/DatasetsAndNotebooksContext";

const PAGE_SIZE = 100;
const VIEWS = ["document", "structure", "images"];
const JUMP_LOOKAHEAD = 25;

function usePagedContent(fetchPage, contentType, enabled) {
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
      append(await fetchPage(contentType, itemsRef.current.length, PAGE_SIZE));
    } catch (error) {
      setFailed(true);
    } finally {
      setLoading(false);
    }
  }, [fetchPage, contentType, append]);

  const loadThrough = useCallback(
    async (position) => {
      try {
        while (
          itemsRef.current.length < totalRef.current &&
          (itemsRef.current.length === 0 ||
            itemsRef.current[itemsRef.current.length - 1].position < position)
        ) {
          append(
            await fetchPage(contentType, itemsRef.current.length, PAGE_SIZE),
          );
        }
      } catch (error) {
        setFailed(true);
      }
    },
    [fetchPage, contentType, append],
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

export default function DocumentReader({
  fetchPage,
  fetchOutline,
  counts = {},
  totalPages = null,
  enabled = true,
}) {
  const { t } = useTranslation(["datasets"]);
  const theme = useTheme();
  const { setRightBarContent } = useDatasetsAndNotebooks();
  const [tab, setTab] = useState(0);
  const [outline, setOutline] = useState(null);
  const [pendingJump, setPendingJump] = useState(null);
  const view = VIEWS[tab];

  const content = usePagedContent(fetchPage, "all", enabled);
  const images = usePagedContent(
    fetchPage,
    "Image",
    enabled && view === "images",
  );
  const { loadThrough } = content;

  useEffect(() => {
    if (!enabled) return undefined;
    let cancelled = false;
    fetchOutline()
      .then((body) => {
        if (!cancelled) setOutline(body.items);
      })
      .catch(() => {
        if (!cancelled) setOutline([]);
      });
    return () => {
      cancelled = true;
    };
  }, [fetchOutline, enabled]);

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

  if (!enabled) return null;

  const active = view === "images" ? images : content;

  return (
    <>
      <DocumentHeader
        totalPages={totalPages}
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

        {!active.loading && !active.failed && active.items.length === 0 && (
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
  );
}

DocumentReader.propTypes = {
  fetchPage: PropTypes.func.isRequired,
  fetchOutline: PropTypes.func.isRequired,
  counts: PropTypes.objectOf(PropTypes.number),
  totalPages: PropTypes.number,
  enabled: PropTypes.bool,
};
