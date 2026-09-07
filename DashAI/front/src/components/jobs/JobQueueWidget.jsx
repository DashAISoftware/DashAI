import React, { useState, useEffect, useCallback, useRef } from "react";
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Box,
  Paper,
  Typography,
  IconButton,
  Badge,
  Collapse,
  List,
  LinearProgress,
  CircularProgress,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  ListItemSecondaryAction,
  Tooltip,
  Fade,
  Divider,
  Chip,
} from "@mui/material";
import CloseIcon from "@mui/icons-material/Close";
import { deleteJob } from "../../api/job";
import TaskAltIcon from "@mui/icons-material/TaskAlt";
import KeyboardArrowUpIcon from "@mui/icons-material/KeyboardArrowUp";
import KeyboardArrowDownIcon from "@mui/icons-material/KeyboardArrowDown";
import HourglassEmptyIcon from "@mui/icons-material/HourglassEmpty";
import PlayArrowIcon from "@mui/icons-material/PlayArrow";
import CheckCircleIcon from "@mui/icons-material/CheckCircle";
import ErrorIcon from "@mui/icons-material/Error";
import DeleteIcon from "@mui/icons-material/Delete";
import MoreHorizIcon from "@mui/icons-material/MoreHoriz";
import RefreshIcon from "@mui/icons-material/Refresh";
import JobDetailsDialog from "./JobDetailsDialog";
import DeleteSweepIcon from "@mui/icons-material/DeleteSweep";
import DragIndicatorIcon from "@mui/icons-material/DragIndicator";
import { deleteAllJobs } from "../../api/job";
import { useJobManager } from "../../hooks/useJobPolling";
import { useTranslation } from "react-i18next";
import { getStatusText } from "../../utils/jobStatusText";

export const StatusIcon = ({ status }) => {
  switch (status) {
    case "not_started":
      return <HourglassEmptyIcon fontSize="small" />;
    case "started":
      return <PlayArrowIcon fontSize="small" color="primary" />;
    case "finished":
      return <CheckCircleIcon fontSize="small" color="success" />;
    case "error":
      return <ErrorIcon fontSize="small" color="error" />;
    case "deleted":
      return <DeleteIcon fontSize="small" />;
    default:
      return <MoreHorizIcon fontSize="small" />;
  }
};

const JobQueueWidget = () => {
  const { t } = useTranslation(["common"]);
  const [expanded, setExpanded] = useState(() => {
    try {
      const savedState = localStorage.getItem("jobQueueWidgetExpanded");
      return savedState === "true";
    } catch (e) {
      return false;
    }
  });
  const [selectedJob, setSelectedJob] = useState(null);
  const [showFinished, setShowFinished] = useState(false);
  const [jobToDelete, setJobToDelete] = useState(null);
  const [confirmClearAll, setConfirmClearAll] = useState(false);
  const [clearingAll, setClearingAll] = useState(false);
  const [forceUpdate, setForceUpdate] = useState(0);
  const [isHovered, setIsHovered] = useState(false);

  // Drag state — anchored to whichever edge (left/right, top/bottom) is
  // nearest, as a distance in px from that edge. This is what lets the
  // default (never-dragged) position sit at a fixed spot regardless of
  // browser zoom: `right`/`bottom` distances don't change when the viewport
  // shrinks or grows. Storing dragged positions as left/top instead (an
  // older version of this code did) broke that: the widget would visibly
  // slide as zoom changed, since its true offset was measured from the
  // opposite (far) edge.
  const [position, setPosition] = useState(() => {
    try {
      const saved = localStorage.getItem("jobQueueWidgetPosition");
      if (!saved) return null;
      const parsed = JSON.parse(saved);
      // Discard positions saved by the old left/top-based format.
      if (parsed && "horizontal" in parsed && "vertical" in parsed) {
        return parsed;
      }
      return null;
    } catch {
      return null;
    }
  });
  const dragRef = useRef(null);
  const isDragging = useRef(false);

  const handleDragStart = useCallback((e) => {
    // Ignore if clicking on buttons/icons inside the header
    if (e.target.closest("button") || e.target.closest("[role='button']"))
      return;
    e.preventDefault();
    isDragging.current = false;
    const paperEl = dragRef.current;
    if (!paperEl) return;
    const rect = paperEl.getBoundingClientRect();
    const offsetX = e.clientX - rect.left;
    const offsetY = e.clientY - rect.top;

    const handleMouseMove = (moveEvent) => {
      isDragging.current = true;
      const newLeft = Math.max(
        0,
        Math.min(moveEvent.clientX - offsetX, window.innerWidth - rect.width),
      );
      const newTop = Math.max(
        0,
        Math.min(moveEvent.clientY - offsetY, window.innerHeight - rect.height),
      );

      // Anchor to whichever half of the screen the widget is closer to, so
      // its distance from that edge (not from the opposite one) is what
      // gets persisted and re-rendered.
      const isRightHalf = newLeft + rect.width / 2 > window.innerWidth / 2;
      const isLowerHalf = newTop + rect.height / 2 > window.innerHeight / 2;

      setPosition({
        horizontal: isRightHalf ? "right" : "left",
        h: isRightHalf ? window.innerWidth - newLeft - rect.width : newLeft,
        vertical: isLowerHalf ? "bottom" : "top",
        v: isLowerHalf ? window.innerHeight - newTop - rect.height : newTop,
      });
    };

    const handleMouseUp = () => {
      document.removeEventListener("mousemove", handleMouseMove);
      document.removeEventListener("mouseup", handleMouseUp);
    };

    document.addEventListener("mousemove", handleMouseMove);
    document.addEventListener("mouseup", handleMouseUp);
  }, []);

  // Persist drag position
  useEffect(() => {
    if (position) {
      try {
        localStorage.setItem(
          "jobQueueWidgetPosition",
          JSON.stringify(position),
        );
      } catch {
        // ignore
      }
    }
  }, [position]);

  // Safety net only: an edge-anchored offset stays valid across zoom by
  // design, but an extreme window resize (viewport now narrower/shorter
  // than the widget itself) could still push it out of bounds, so re-clamp
  // on mount and on resize.
  useEffect(() => {
    const clampToViewport = () => {
      setPosition((prev) => {
        if (!prev) return prev;
        const rect = dragRef.current?.getBoundingClientRect();
        const width = rect?.width ?? 320;
        const height = rect?.height ?? 56;
        const maxH = Math.max(0, window.innerWidth - width);
        const maxV = Math.max(0, window.innerHeight - height);
        const clampedH = Math.min(Math.max(prev.h, 0), maxH);
        const clampedV = Math.min(Math.max(prev.v, 0), maxV);
        if (clampedH === prev.h && clampedV === prev.v) return prev;
        return { ...prev, h: clampedH, v: clampedV };
      });
    };

    clampToViewport();
    window.addEventListener("resize", clampToViewport);
    return () => window.removeEventListener("resize", clampToViewport);
  }, []);

  const handleClearAllJobs = () => {
    setConfirmClearAll(true);
  };

  const confirmClearAllJobs = async () => {
    try {
      setClearingAll(true);
      await deleteAllJobs();
      refresh();
      setTimeout(() => {
        refresh();
        setClearingAll(false);
        setConfirmClearAll(false);
      }, 500);
    } catch (error) {
      console.error("Error clearing all jobs:", error);
      setClearingAll(false);
      setConfirmClearAll(false);
    }
  };

  const cancelClearAllJobs = () => {
    setConfirmClearAll(false);
  };

  const handleDeleteJob = (job) => {
    setJobToDelete(job);
  };

  const confirmDeleteJob = async () => {
    if (!jobToDelete) return;

    try {
      await deleteJob(jobToDelete.id);

      setTimeout(() => {
        refresh();
      }, 500);
    } catch (error) {
      console.error("Error deleting job:", error);
    } finally {
      setJobToDelete(null);
    }
  };

  const cancelDeleteJob = () => {
    setJobToDelete(null);
  };

  const { jobs, loading, error, refresh } = useJobManager();

  const activeJobs = jobs.filter(
    (job) => job.status === "started" || job.status === "not_started",
  );
  const finishedJobs = jobs.filter((job) => job.status === "finished");
  const errorJobs = jobs.filter((job) => job.status === "error");

  const hasInitializedRef = useRef(false);
  const prevActiveCountRef = useRef(0);

  // Snapshot initial state after first load completes (prevents treating
  // existing jobs as new and triggering expand on mount)
  useEffect(() => {
    if (!loading && !hasInitializedRef.current) {
      hasInitializedRef.current = true;
      prevActiveCountRef.current = activeJobs.length;
    }
  }, [loading, activeJobs.length]);

  // Auto expand/collapse on real transitions during session
  useEffect(() => {
    if (!hasInitializedRef.current) return;
    const prev = prevActiveCountRef.current;
    const curr = activeJobs.length;
    if (prev === 0 && curr > 0) {
      setExpanded(true);
    } else if (prev > 0 && curr === 0) {
      setExpanded(false);
    }
    prevActiveCountRef.current = curr;
  }, [activeJobs.length]);

  useEffect(() => {
    try {
      localStorage.setItem("jobQueueWidgetExpanded", String(expanded));
    } catch (e) {
      // ignore
    }
  }, [expanded]);

  const handleToggleExpand = () => {
    setExpanded(!expanded);
  };

  const handleJobClick = (job) => {
    setSelectedJob(job);
  };

  const handleCloseDetails = () => {
    setSelectedJob(null);
  };

  const handleRefresh = () => {
    setForceUpdate((prev) => prev + 1);
    refresh();
  };

  const parseTimestamp = (ts) =>
    ts
      ? ts.includes("T")
        ? new Date(ts)
        : new Date(ts.replace(" ", "T") + "Z")
      : new Date(0);

  const getJobsToShow = () => {
    if (showFinished) {
      return [...jobs]
        .sort(
          (a, b) =>
            parseTimestamp(b.last_update) - parseTimestamp(a.last_update),
        )
        .slice(0, 25);
    }

    return [...activeJobs]
      .sort(
        (a, b) => parseTimestamp(b.last_update) - parseTimestamp(a.last_update),
      )
      .slice(0, 10);
  };

  const getRelativeTime = useCallback(
    (timestamp) => {
      try {
        const date = timestamp.includes("T")
          ? new Date(timestamp)
          : new Date(timestamp.replace(" ", "T") + "Z");

        const now = new Date();
        const diffSeconds = Math.floor((now - date) / 1000);

        if (diffSeconds < 0) {
          if (diffSeconds > -60)
            return t("common:jobQueue.relativeTime.justNow");

          const absDiff = Math.abs(diffSeconds);
          if (absDiff < 60)
            return t("common:jobQueue.relativeTime.inSeconds", {
              count: absDiff,
            });
          if (absDiff < 3600)
            return t("common:jobQueue.relativeTime.inMinutes", {
              count: Math.floor(absDiff / 60),
            });
          if (absDiff < 86400)
            return t("common:jobQueue.relativeTime.inHours", {
              count: Math.floor(absDiff / 3600),
            });
          return t("common:jobQueue.relativeTime.inDays", {
            count: Math.floor(absDiff / 86400),
          });
        }

        if (diffSeconds < 30) return t("common:jobQueue.relativeTime.justNow");
        if (diffSeconds < 60)
          return t("common:jobQueue.relativeTime.secondsAgo", {
            count: diffSeconds,
          });
        if (diffSeconds < 3600)
          return t("common:jobQueue.relativeTime.minutesAgo", {
            count: Math.floor(diffSeconds / 60),
          });
        if (diffSeconds < 86400)
          return t("common:jobQueue.relativeTime.hoursAgo", {
            count: Math.floor(diffSeconds / 3600),
          });
        return t("common:jobQueue.relativeTime.daysAgo", {
          count: Math.floor(diffSeconds / 86400),
        });
      } catch (e) {
        console.error("Error parsing time:", e, timestamp);
        return t("common:jobQueue.relativeTime.unknown");
      }
    },
    [forceUpdate, t],
  );

  const jobsToShow = getJobsToShow();
  //filter: `brightness(${isHovered || expanded ? 1 : 0.7})`,
  return (
    <>
      <Fade in={true}>
        <Paper
          ref={dragRef}
          elevation={0}
          onMouseEnter={() => setIsHovered(true)}
          onMouseLeave={() => setIsHovered(false)}
          sx={{
            position: "fixed",
            ...(position
              ? {
                  [position.horizontal]: position.h,
                  [position.vertical]: position.v,
                }
              : {
                  bottom: { xs: 16, sm: (theme) => theme.spacing(3) },
                  right: { xs: 16, sm: (theme) => theme.spacing(3) },
                }),
            zIndex: 1300,
            width: { xs: "calc(100vw - 32px)", sm: 320 },
            maxWidth: 320,
            maxHeight: { xs: "60vh", sm: "80vh" },
            display: "flex",
            flexDirection: "column",
            boxShadow: (theme) => theme.shadows[6],
            borderRadius: (theme) => theme.shape.borderRadius,
            overflow: "hidden",
            bgcolor: "background.box",
            color: "text.primary",
            backgroundImage: "none",
          }}
          style={{
            opacity: `${isHovered || expanded ? 1 : 0.5}`,
            filter: `brightness(${isHovered || expanded ? 1 : 0.5})`,
            transition: isDragging.current ? "none" : "all 0.2s ease",
          }}
        >
          <Box
            onMouseDown={handleDragStart}
            onClick={(e) => {
              if (!isDragging.current) handleToggleExpand();
            }}
            sx={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              padding: (theme) => theme.spacing(1, 2),
              backgroundColor: (theme) => theme.palette.primary.main,
              color: (theme) => theme.palette.primary.contrastText,
              cursor: "grab",
              "&:active": { cursor: "grabbing" },
            }}
          >
            <Box display="flex" alignItems="center">
              <Tooltip title="Drag to move · Double-click to reset">
                <DragIndicatorIcon
                  fontSize="small"
                  sx={{ opacity: 0.6, mr: 1 }}
                  onDoubleClick={(e) => {
                    e.stopPropagation();
                    setPosition(null);
                    localStorage.removeItem("jobQueueWidgetPosition");
                  }}
                />
              </Tooltip>
              <Badge
                badgeContent={activeJobs.length}
                color="error"
                sx={{ mr: 3 }}
              >
                <TaskAltIcon />
              </Badge>
              <Typography variant="subtitle1" sx={{ fontWeight: "medium" }}>
                {t("common:jobQueue.title")}
              </Typography>
            </Box>
            <Box display="flex" alignItems="center">
              {jobs.length > 0 && (
                <Tooltip title={t("common:jobQueue.clearAllJobs")}>
                  <IconButton
                    size="small"
                    onClick={(e) => {
                      e.stopPropagation();
                      handleClearAllJobs();
                    }}
                    sx={{
                      color: "primary.contrastText",
                      opacity: 0.8,
                      mr: 1,
                    }}
                  >
                    <DeleteSweepIcon fontSize="small" />
                  </IconButton>
                </Tooltip>
              )}
              <Tooltip title={t("common:jobQueue.refresh")}>
                <IconButton
                  size="small"
                  onClick={(e) => {
                    e.stopPropagation();
                    handleRefresh();
                  }}
                  sx={{ color: "primary.contrastText", opacity: 0.8, mr: 1 }}
                >
                  <RefreshIcon fontSize="small" />
                </IconButton>
              </Tooltip>
              {expanded ? (
                <KeyboardArrowDownIcon fontSize="small" />
              ) : (
                <KeyboardArrowUpIcon fontSize="small" />
              )}
            </Box>
          </Box>

          <Collapse in={expanded} timeout="auto">
            <Box
              sx={{
                display: "flex",
                flexDirection: "column",
                backgroundColor: "background.box",
              }}
            >
              <Box
                sx={{
                  maxHeight: { xs: 180, sm: 280 },
                  overflowY: "auto",
                }}
              >
                {loading && jobs.length === 0 && (
                  <Box display="flex" justifyContent="center" p={2}>
                    <Typography variant="body2" color="text.secondary">
                      {t("common:loading")}
                    </Typography>
                  </Box>
                )}

                {error && (
                  <Box p={2}>
                    <Typography variant="body2" color="error">
                      {t("common:error")}: {error}
                    </Typography>
                  </Box>
                )}

                {jobsToShow.length === 0 && !loading && !error && (
                  <Box display="flex" justifyContent="center" p={2}>
                    <Typography variant="body2" color="text.secondary">
                      {showFinished
                        ? t("common:jobQueue.noJobs")
                        : t("common:jobQueue.noActiveJobs")}
                    </Typography>
                  </Box>
                )}

                {jobsToShow.length > 0 && (
                  <List dense disablePadding>
                    {jobsToShow.map((job) => (
                      <ListItem key={job.id} disablePadding divider>
                        <ListItemButton
                          onClick={() => handleJobClick(job)}
                          sx={{
                            pr: 8,
                            bgcolor:
                              job.status === "started"
                                ? "action.selected"
                                : "transparent",
                            "&:hover": {
                              bgcolor:
                                job.status === "started"
                                  ? "action.selected"
                                  : "action.hover",
                            },
                          }}
                        >
                          <ListItemIcon sx={{ minWidth: 40 }}>
                            <StatusIcon status={job.status} />
                          </ListItemIcon>
                          <ListItemText
                            secondaryTypographyProps={{ component: "div" }}
                            primary={
                              <Box display="flex" alignItems="center">
                                <Tooltip title={job.job_name || ""}>
                                  <Typography variant="body2" noWrap>
                                    {job.job_name
                                      ? job.job_name
                                      : job.task_type
                                        ? job.task_type.split(".").pop()
                                        : t("common:unknown")}
                                  </Typography>
                                </Tooltip>
                              </Box>
                            }
                            secondary={
                              <Box component="span" sx={{ display: "block" }}>
                                <Typography
                                  variant="caption"
                                  component="span"
                                  color="text.secondary"
                                  sx={{ display: "flex", alignItems: "center" }}
                                >
                                  <span>
                                    {job.status === "started" &&
                                    job.progress_message
                                      ? job.progress_message
                                      : getStatusText(job.status, t)}
                                  </span>
                                  {job.status === "error" && (
                                    <Tooltip
                                      title={
                                        job.error_msg ||
                                        t("common:unknownError")
                                      }
                                    >
                                      <ErrorIcon
                                        fontSize="inherit"
                                        color="error"
                                        sx={{ ml: 1, fontSize: "1rem" }}
                                      />
                                    </Tooltip>
                                  )}
                                </Typography>
                                {job.status === "started" && (
                                  <LinearProgress
                                    variant={
                                      job.progress != null
                                        ? "determinate"
                                        : "indeterminate"
                                    }
                                    value={
                                      job.progress != null
                                        ? job.progress
                                        : undefined
                                    }
                                    sx={{
                                      mt: 0.5,
                                      height: 4,
                                      borderRadius: 1,
                                    }}
                                  />
                                )}
                              </Box>
                            }
                          />
                        </ListItemButton>
                        <ListItemSecondaryAction>
                          <Box display="flex" alignItems="center">
                            <Typography
                              variant="caption"
                              color="text.secondary"
                              sx={{ mr: 2 }}
                            >
                              {getRelativeTime(job.last_update)}
                            </Typography>
                            {job.status !== "deleted" && (
                              <Tooltip
                                title={
                                  job.status === "started"
                                    ? t("common:jobQueue.cancelJob")
                                    : t("common:jobQueue.deleteJob")
                                }
                              >
                                <IconButton
                                  edge="end"
                                  aria-label="delete"
                                  size="small"
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    handleDeleteJob(job);
                                  }}
                                  sx={{ opacity: 0.7 }}
                                >
                                  <CloseIcon fontSize="small" />
                                </IconButton>
                              </Tooltip>
                            )}
                          </Box>
                        </ListItemSecondaryAction>
                      </ListItem>
                    ))}
                  </List>
                )}
              </Box>

              {/* Panel fijo para los controles */}
              {jobs.length > 0 && (
                <>
                  <Divider />
                  <Box
                    display="flex"
                    justifyContent="space-between"
                    alignItems="center"
                    p={1}
                    sx={{
                      borderTop: "1px solid",
                      borderTopColor: "divider",
                    }}
                  >
                    <Box display="flex" gap={0.5}>
                      <Chip
                        label={t("common:jobQueue.activeCount", {
                          count: activeJobs.length,
                        })}
                        size="small"
                        color="primary"
                        variant="outlined"
                      />
                      <Chip
                        label={t("common:jobQueue.failedCount", {
                          count: errorJobs.length,
                        })}
                        size="small"
                        color="error"
                        variant="outlined"
                      />
                    </Box>

                    <Chip
                      label={
                        showFinished
                          ? t("common:jobQueue.hideCompleted")
                          : t("common:jobQueue.showCompleted")
                      }
                      size="small"
                      onClick={(e) => {
                        e.stopPropagation();
                        setShowFinished(!showFinished);
                      }}
                      clickable
                    />
                  </Box>
                </>
              )}
            </Box>
          </Collapse>
        </Paper>
      </Fade>

      <JobDetailsDialog
        job={selectedJob}
        open={Boolean(selectedJob)}
        onClose={handleCloseDetails}
      />

      <Dialog
        open={Boolean(jobToDelete)}
        onClose={cancelDeleteJob}
        aria-labelledby="delete-job-dialog-title"
      >
        <DialogTitle id="delete-job-dialog-title">
          {t("common:jobQueue.deleteJob")}
        </DialogTitle>
        <DialogContent>
          <Typography>
            {t("common:jobQueue.confirmDeleteJob")}
            {jobToDelete && (
              <Box component="span" fontWeight="bold" display="block" mt={1}>
                {jobToDelete.job_name ||
                  jobToDelete.task_type ||
                  t("common:unknown")}
              </Box>
            )}
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={cancelDeleteJob} color="primary">
            {t("common:cancel")}
          </Button>
          <Button onClick={confirmDeleteJob} color="error">
            {t("common:delete")}
          </Button>
        </DialogActions>
      </Dialog>

      <Dialog
        open={confirmClearAll}
        onClose={cancelClearAllJobs}
        aria-labelledby="clear-all-dialog-title"
      >
        <DialogTitle id="clear-all-dialog-title">
          {t("common:jobQueue.clearAllJobs")}
        </DialogTitle>
        <DialogContent>
          <Typography>
            {t("common:jobQueue.confirmClearAll")}
            <Box component="span" fontWeight="bold" display="block" mt={1}>
              {t("common:jobQueue.confirmClearAllDetail")}
            </Box>
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button
            onClick={cancelClearAllJobs}
            color="primary"
            disabled={clearingAll}
          >
            {t("common:cancel")}
          </Button>
          <Button
            onClick={confirmClearAllJobs}
            color="error"
            disabled={clearingAll}
            startIcon={clearingAll ? <CircularProgress size={20} /> : null}
          >
            {clearingAll
              ? t("common:jobQueue.clearing")
              : t("common:jobQueue.clearAll")}
          </Button>
        </DialogActions>
      </Dialog>
    </>
  );
};

export default JobQueueWidget;
