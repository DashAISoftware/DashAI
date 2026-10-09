import React, { useCallback, useEffect, useRef, useState } from "react";
import PropTypes from "prop-types";
import { Box, CircularProgress, Typography } from "@mui/material";
import { useSnackbar } from "notistack";
import { useTranslation } from "react-i18next";

import { getReports, deleteReport } from "../../../api/report";
import { getComponents } from "../../../api/component";
import ReportCard from "../../reports/ReportCard";

/** Statuses that mean a report job is still outstanding. */
const IN_FLIGHT = [1, 2];

/** How often the list refreshes while any report is still computing. */
const POLL_INTERVAL_MS = 3000;

/**
 * Lists the evaluation reports created for a run, oldest first so the newest
 * lands at the bottom. New ones are added from the right sidebar, mirroring
 * how explainers are added and ordered.
 */
export default function ReportResultsTab({ run, session, refreshTrigger }) {
  const { t } = useTranslation(["reports"]);
  const { enqueueSnackbar } = useSnackbar();

  const [reports, setReports] = useState([]);
  const [displayNames, setDisplayNames] = useState({});
  const [loading, setLoading] = useState(true);
  // A just added report: pendingScroll brings it into view, highlightedId
  // drives the ring. Both are keyed by id so a poll that returns the same rows
  // cannot replay either.
  const [pendingScroll, setPendingScroll] = useState(null);
  const [highlightedId, setHighlightedId] = useState(null);
  // null until the first fetch lands, so the first render can tell "opened the
  // tab" (jump to the bottom) apart from "a report was added" (glide to it).
  const seenIdsRef = useRef(null);

  const fetchReports = useCallback(async () => {
    try {
      const response = await getReports(run.id);
      // Oldest first, so a newly added report lands at the bottom of the list
      // the way a newly added explainer does.
      const ordered = [...response].sort((a, b) => a.id - b.id);
      setReports(ordered);

      const ids = ordered.map((item) => item.id);
      const newest = ids[ids.length - 1] ?? null;
      if (seenIdsRef.current === null) {
        // Opening the tab lands at the bottom, matching the explainer list.
        if (newest !== null) setPendingScroll({ id: newest, smooth: false });
      } else {
        const added = ids.filter((id) => !seenIdsRef.current.has(id));
        if (added.length > 0) {
          const addedNewest = added[added.length - 1];
          setPendingScroll({ id: addedNewest, smooth: true });
          setHighlightedId(addedNewest);
        }
      }
      seenIdsRef.current = new Set(ids);
    } catch (error) {
      console.error("Error fetching reports:", error);
      enqueueSnackbar(t("reports:error.fetch"), { variant: "error" });
    }
  }, [run.id, enqueueSnackbar, t]);

  // Only the very first load shows a spinner. Flipping it back on for every
  // refresh would unmount the whole list and replace it with a spinner each
  // time a report is added and again when its job lands, which reads as lag
  // rather than as progress. Later fetches swap the rows in place.
  useEffect(() => {
    fetchReports().finally(() => setLoading(false));
  }, [fetchReports, refreshTrigger]);

  // Component display names are resolved once per task so each card can show a
  // human readable title instead of the registry key.
  useEffect(() => {
    if (!session?.task_name) return;
    getComponents({
      selectTypes: ["Report"],
      relatedComponent: session.task_name,
    })
      .then((components) =>
        setDisplayNames(
          Object.fromEntries(
            components.map((item) => [
              item.name,
              item.display_name || item.name,
            ]),
          ),
        ),
      )
      .catch((error) => console.error("Error fetching report names:", error));
  }, [session?.task_name]);

  // The card has to exist before it can be scrolled to, so this waits a beat
  // after the list renders, the way the explainer tab does.
  useEffect(() => {
    if (!pendingScroll) return undefined;
    const timer = setTimeout(() => {
      const element = document.getElementById(
        `report-card-${pendingScroll.id}`,
      );
      if (element) {
        element.scrollIntoView({
          block: "end",
          behavior: pendingScroll.smooth ? "smooth" : "auto",
        });
      }
      setPendingScroll(null);
    }, 100);
    return () => clearTimeout(timer);
  }, [pendingScroll, reports]);

  // Clear the highlight after the animation, in its own effect so nothing else
  // cancels the timer and leaves the card flagged, replaying the ring on every
  // remount.
  useEffect(() => {
    if (!highlightedId) return undefined;
    const timer = setTimeout(() => setHighlightedId(null), 4000);
    return () => clearTimeout(timer);
  }, [highlightedId]);

  const anyRunning = reports.some((item) => IN_FLIGHT.includes(item.status));

  useEffect(() => {
    if (!anyRunning) return undefined;
    const handle = setInterval(fetchReports, POLL_INTERVAL_MS);
    return () => clearInterval(handle);
  }, [anyRunning, fetchReports]);

  const handleDelete = async (report) => {
    try {
      await deleteReport(report.id);
      setReports((prev) => prev.filter((item) => item.id !== report.id));
    } catch (error) {
      console.error("Error deleting report:", error);
      enqueueSnackbar(t("reports:error.delete"), { variant: "error" });
    }
  };

  if (loading) {
    return (
      <Box sx={{ display: "flex", justifyContent: "center", py: 6 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (reports.length === 0) {
    return (
      <Box sx={{ py: 6, textAlign: "center" }}>
        <Typography variant="body2" color="text.secondary">
          {t("reports:message.empty")}
        </Typography>
      </Box>
    );
  }

  return (
    // px gives the highlight ring room so the scroller does not clip its sides.
    <Box
      sx={{ py: 4, px: 1.5, display: "flex", flexDirection: "column", gap: 3 }}
    >
      {reports.map((report) => (
        <ReportCard
          key={report.id}
          report={report}
          displayName={displayNames[report.report_name]}
          onDelete={handleDelete}
          isHighlighted={highlightedId === report.id}
        />
      ))}
    </Box>
  );
}

ReportResultsTab.propTypes = {
  run: PropTypes.shape({
    id: PropTypes.number.isRequired,
  }).isRequired,
  session: PropTypes.shape({
    task_name: PropTypes.string,
  }),
  refreshTrigger: PropTypes.number,
};
