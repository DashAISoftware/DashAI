import { useCallback, useEffect, useState } from "react";
import PropTypes from "prop-types";
import {
  Alert,
  Box,
  Button,
  CircularProgress,
  Divider,
  Grid,
  Stack,
  Tab,
  Typography,
} from "@mui/material";
import { AddCircleOutline as AddIcon } from "@mui/icons-material";
import { useTranslation } from "react-i18next";
import PillTabs from "../shared/PillTabs";
import DocumentRightBar from "./DocumentRightBar";
import DocumentHeader from "./DocumentHeader";
import DocumentRenderer from "./DocumentRenderer";
import { getDocumentContent } from "../../api/documents";
import { DOCUMENT_STATUS } from "../../hooks/datasets/useDocuments";
import { formatDate } from "../../pages/results/constants/formatDate";
import { useDatasetsAndNotebooks } from "../custom/contexts/DatasetsAndNotebooksContext";

const PAGE_SIZE = 50;
const CONTENT_TABS = ["all", "Text", "Image"];

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
    setRightBarContent(<DocumentRightBar />);
    return () => setRightBarContent(null);
  }, [setRightBarContent]);

  const loadPage = useCallback(
    async (offset) => {
      if (!contentType) return;
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
    if (!isFinished || !contentType) {
      setItems([]);
      setTotal(0);
      return;
    }
    loadPage(0);
  }, [isFinished, contentType, loadPage]);

  if (!dataDocument) {
    return (
      <Box sx={{ display: "flex", justifyContent: "center", pt: 8 }}>
        <CircularProgress />
      </Box>
    );
  }

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
              fileType={dataDocument.file_type}
            />

            <PillTabs
              minHeight="48px"
              value={tab}
              onChange={(_, value) => setTab(value)}
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

            <Divider sx={{ my: 4 }} />

            <Stack spacing={2}>
              {failed && (
                <Alert severity="error">
                  {t("datasets:document.loadingFailed")}
                </Alert>
              )}
              <DocumentRenderer items={items} />
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
          </>
        )}
      </Box>
    </Box>
  );
}

DocumentView.propTypes = { dataDocument: PropTypes.object };
