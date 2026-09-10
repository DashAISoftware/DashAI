import { useState, useEffect } from "react";
import { Navigate, useParams } from "react-router-dom";
import { Box, CircularProgress, Typography } from "@mui/material";
import { useTranslation } from "react-i18next";
import { getGenerativeSession } from "../../api/generativeTask";
import { RAG_TASK_NAME } from "../../api/rag";
import Generative from "./Generative";

/**
 * Route a generic session URL to the right view.
 *
 * Tasks with their own entry point live under that entry point's URL, so a RAG
 * session reached through the shared `/sessions/:id` path is redirected to its
 * canonical address rather than rendered here. Older links therefore keep
 * working while there is only one URL per session.
 *
 * @returns {JSX.Element} The session view, a redirect, or a loading indicator.
 */
export default function SessionRouter() {
  const { id } = useParams();
  const { t } = useTranslation(["generative"]);
  const [taskName, setTaskName] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const sessionId = Number(id);
    if (!Number.isFinite(sessionId) || sessionId <= 0) {
      setTaskName(null);
      setLoading(false);
      return;
    }

    let cancelled = false;
    setLoading(true);

    getGenerativeSession(sessionId)
      .then((session) => {
        if (!cancelled) setTaskName(session?.task_name || null);
      })
      .catch(() => {
        if (!cancelled) setTaskName(null);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [id]);

  if (loading) {
    return (
      <Box
        display="flex"
        alignItems="center"
        justifyContent="center"
        height="100vh"
      >
        <CircularProgress />
      </Box>
    );
  }

  if (!taskName) {
    return (
      <Box
        display="flex"
        alignItems="center"
        justifyContent="center"
        height="100vh"
      >
        <Typography variant="h6" color="text.secondary">
          {t("generative:rag.session.notFound")}
        </Typography>
      </Box>
    );
  }

  if (taskName === RAG_TASK_NAME) {
    return <Navigate to={`/app/generative/rag/sessions/${id}`} replace />;
  }

  return <Generative key={id} />;
}
