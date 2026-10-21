import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import PropTypes from "prop-types";
import {
  Alert,
  Box,
  Button,
  CircularProgress,
  Grid,
  Typography,
} from "@mui/material";
import { useTheme } from "@mui/material/styles";
import { AddCircleOutline as AddIcon } from "@mui/icons-material";
import { useTranslation } from "react-i18next";
import DocumentRightBar from "./DocumentRightBar";
import DocumentHeader from "./DocumentHeader";
import DocumentToolbar from "./DocumentToolbar";
import DocumentKindFilter from "./DocumentKindFilter";
import DocumentRenderer from "./DocumentRenderer";
import DocumentImageGrid from "./DocumentImageGrid";
import { countKinds, scrollToPage, scrollToPosition } from "./documentKinds";
import { getDocumentContent, getDocumentOutline } from "../../api/documents";
import { DOCUMENT_STATUS } from "../../hooks/datasets/useDocuments";
import { formatDate } from "../../pages/results/constants/formatDate";
import { useDatasetsAndNotebooks } from "../custom/contexts/DatasetsAndNotebooksContext";

const PAGE_SIZE = 100;
const VIEWS = ["document", "structure", "images"];
const JUMP_LOOKAHEAD = 25;
const SPY_MARGIN = "-96px 0px -55% 0px";
const BOTTOM_TOLERANCE = 4;

function scrollParent(element) {
  let node = element.parentElement;
  while (node) {
    const { overflowY } = window.getComputedStyle(node);
    if (overflowY === "auto" || overflowY === "scroll") return node;
    node = node.parentElement;
  }
  return null;
}

function lastVisiblePosition(elements, scroller) {
  const bottom = scroller.getBoundingClientRect().bottom;
  for (let index = elements.length - 1; index >= 0; index -= 1) {
    if (elements[index].getBoundingClientRect().top < bottom) {
      return Number(elements[index].dataset.documentPosition);
    }
  }
  return null;
}

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

function useVisiblePosition(containerRef, enabled, renderKey) {
  const [position, setPosition] = useState(null);
  useEffect(() => {
    const container = containerRef.current;
    if (!enabled || !container || !window.IntersectionObserver) {
      return undefined;
    }
    const elements = container.querySelectorAll("[data-document-position]");
    const scroller = scrollParent(container);
    const visible = new Set();
    let frame = 0;
    let reported = null;
    const read = () => {
      frame = 0;
      const atBottom =
        scroller &&
        scroller.scrollTop > 0 &&
        scroller.scrollTop + scroller.clientHeight >=
          scroller.scrollHeight - BOTTOM_TOLERANCE;
      let next = null;
      if (atBottom) {
        next = lastVisiblePosition(elements, scroller);
      } else if (visible.size > 0) {
        next = Math.min(...visible);
      }
      if (next !== null && next !== reported) {
        reported = next;
        setPosition(next);
      }
    };
    const update = () => {
      if (!frame) frame = requestAnimationFrame(read);
    };
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          const value = Number(entry.target.dataset.documentPosition);
          if (entry.isIntersecting) visible.add(value);
          else visible.delete(value);
        });
        update();
      },
      { rootMargin: SPY_MARGIN },
    );
    elements.forEach((element) => observer.observe(element));
    scroller?.addEventListener("scroll", update, { passive: true });
    return () => {
      if (frame) cancelAnimationFrame(frame);
      observer.disconnect();
      scroller?.removeEventListener("scroll", update);
    };
  }, [containerRef, enabled, renderKey]);
  return position;
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
  const [showKinds, setShowKinds] = useState(false);
  const [kindFilter, setKindFilter] = useState([]);
  const [outline, setOutline] = useState(null);
  const [pendingJump, setPendingJump] = useState(null);
  const bodyRef = useRef(null);
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

  const kindCounts = useMemo(() => countKinds(outline ?? []), [outline]);
  const pageByPosition = useMemo(
    () => new Map((outline ?? []).map((item) => [item.position, item.page])),
    [outline],
  );
  const pageStarts = useMemo(() => {
    const starts = new Map();
    (outline ?? []).forEach((item) => {
      if (item.page !== null && !starts.has(item.page)) {
        starts.set(item.page, item.position);
      }
    });
    return starts;
  }, [outline]);

  const pages = useMemo(
    () => [...pageStarts.keys()].sort((a, b) => a - b),
    [pageStarts],
  );

  const structureItems = useMemo(
    () =>
      kindFilter.length > 0
        ? content.items.filter((item) => kindFilter.includes(item.kind))
        : content.items,
    [content.items, kindFilter],
  );

  const visiblePosition = useVisiblePosition(
    bodyRef,
    isFinished && view !== "images",
    `${view}-${showKinds}-${content.items.length}-${kindFilter.join()}`,
  );
  const currentPosition = visiblePosition ?? outline?.[0]?.position ?? null;
  const currentPage =
    currentPosition !== null
      ? (pageByPosition.get(currentPosition) ?? null)
      : null;

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
      setPendingJump({ position, page: null });
    },
    [loadThrough],
  );

  const jumpToPage = useCallback(
    async (page) => {
      const position = pageStarts.get(page);
      if (position === undefined) return;
      await loadThrough(position);
      setPendingJump({ position, page });
    },
    [loadThrough, pageStarts],
  );

  const changeKindFilter = useCallback(
    (kinds) => {
      setKindFilter(kinds);
      const first = (outline ?? []).find((item) => kinds.includes(item.kind));
      if (first) loadThrough(first.position);
    },
    [outline, loadThrough],
  );

  const selectKind = useCallback(
    (kind) => {
      setTab(1);
      changeKindFilter([kind]);
    },
    [changeKindFilter],
  );

  useEffect(() => {
    if (pendingJump === null) return undefined;
    const frame = requestAnimationFrame(() => {
      if (pendingJump.page === null || !scrollToPage(pendingJump.page)) {
        for (
          let p = pendingJump.position;
          p < pendingJump.position + JUMP_LOOKAHEAD;
          p += 1
        ) {
          if (scrollToPosition(p, theme.palette.primary.main)) break;
        }
      }
      setPendingJump(null);
    });
    return () => cancelAnimationFrame(frame);
  }, [pendingJump, content.items, tab, theme]);

  useEffect(() => {
    setRightBarContent(
      <DocumentRightBar
        outline={outline}
        currentPosition={view === "images" ? null : currentPosition}
        onJump={jumpTo}
        onSelectKind={selectKind}
      />,
    );
  }, [setRightBarContent, outline, currentPosition, view, jumpTo, selectKind]);

  useEffect(() => () => setRightBarContent(null), [setRightBarContent]);

  if (!dataDocument) {
    return (
      <Box sx={{ display: "flex", justifyContent: "center", pt: 8 }}>
        <CircularProgress />
      </Box>
    );
  }

  const active = view === "images" ? images : content;
  const visibleItems = view === "structure" ? structureItems : active.items;

  return (
    <Box sx={{ display: "flex", flexDirection: "column", mt: 4, mx: 2 }}>
      {(isFinished || isError) && (
        <Box sx={{ display: "flex", flexDirection: "column", gap: 4, mb: 4 }}>
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

          <Box
            sx={{
              display: "flex",
              justifyContent: "space-between",
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

          {isFinished && (
            <DocumentHeader
              totalPages={dataDocument.total_pages}
              textCount={counts.Text}
              imageCount={counts.Image}
            />
          )}
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
            mt: 2,
          }}
        >
          <CircularProgress color="primary" />
          <Typography>{t("datasets:document.processingTitle")}</Typography>
          <Typography variant="body2" color="text.secondary" textAlign="center">
            {t("datasets:document.processingMessage")}
          </Typography>
        </Box>
      )}

      {isFinished && (
        <>
          <DocumentToolbar
            tab={tab}
            onTabChange={setTab}
            imageCount={counts.Image ?? 0}
            showKinds={showKinds}
            onShowKindsChange={setShowKinds}
            page={currentPage}
            totalPages={dataDocument.total_pages ?? pages.length}
            pages={pages}
            onPageChange={jumpToPage}
          />

          <Box ref={bodyRef} sx={{ mt: 3, mb: 4 }}>
            {active.failed && (
              <Alert severity="error" sx={{ mb: 2 }}>
                {t("datasets:document.loadingFailed")}
              </Alert>
            )}

            {view === "structure" && outline && outline.length > 0 && (
              <DocumentKindFilter
                counts={kindCounts}
                selected={kindFilter}
                onChange={changeKindFilter}
                shown={structureItems.length}
              />
            )}

            {!active.loading && !active.failed && visibleItems.length === 0 && (
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
                <DocumentRenderer
                  items={content.items}
                  mode="read"
                  showKinds={showKinds}
                  totalPages={dataDocument.total_pages}
                />
              </Box>
            )}

            {view === "structure" && structureItems.length > 0 && (
              <DocumentRenderer items={structureItems} mode="structure" />
            )}

            {view === "images" && images.items.length > 0 && (
              <DocumentImageGrid images={images.items} onOpen={jumpTo} />
            )}

            <LoadMoreFooter content={active} />
          </Box>
        </>
      )}
    </Box>
  );
}

DocumentView.propTypes = { dataDocument: PropTypes.object };
