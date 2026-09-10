import React, { useState, useEffect } from "react";
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Typography,
  Grid,
  Chip,
  Paper,
  Box,
  Divider,
  CircularProgress,
  LinearProgress,
} from "@mui/material";
import { useTranslation } from "react-i18next";
import { getJobDetails } from "../../api/job";
import { formatDate } from "../../utils";
import { getStatusText } from "../../utils/jobStatusText";

const JobDetailsDialog = ({ job, open, onClose }) => {
  const { t } = useTranslation(["common"]);
  const [jobDetails, setJobDetails] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (job && job.id && open) {
      setLoading(true);

      const fetchDetails = async () => {
        try {
          const data = await getJobDetails(job.id);
          setJobDetails({ ...job, ...data });
        } catch (error) {
          console.error("Error fetching job details:", error);
          setJobDetails(job);
        } finally {
          setLoading(false);
        }
      };

      fetchDetails();
    } else {
      setJobDetails(job);
    }
  }, [job?.id, open]);

  if (!job) return null;

  const displayJob = jobDetails || job;

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>
        {t("common:jobQueue.details.title")}
        <Chip
          label={getStatusText(displayJob.status, t)}
          color={
            displayJob.status === "finished"
              ? "success"
              : displayJob.status === "error"
                ? "error"
                : displayJob.status === "started"
                  ? "primary"
                  : displayJob.status === "deleted"
                    ? "warning"
                    : "default"
          }
          size="small"
          sx={{ ml: 2 }}
        />
      </DialogTitle>

      <DialogContent>
        {loading ? (
          <Box display="flex" justifyContent="center" my={4}>
            <CircularProgress />
          </Box>
        ) : (
          <Grid container spacing={4}>
            <Grid size={{ xs: 12 }}>
              <Typography
                variant="subtitle2"
                sx={{ fontWeight: "bold", color: "text.secondary" }}
              >
                {t("common:jobQueue.details.jobId")}
              </Typography>
              <Typography
                variant="body1"
                sx={{
                  wordBreak: "break-word",
                  fontFamily: (theme) => theme.typography.fontFamily,
                }}
              >
                {displayJob.entity_id || t("common:na")}
              </Typography>
            </Grid>

            <Grid size={{ xs: 12, md: 6 }}>
              <Typography
                variant="subtitle2"
                sx={{ fontWeight: "bold", color: "text.secondary" }}
              >
                {t("common:jobQueue.details.jobName")}
              </Typography>
              <Typography
                variant="body1"
                sx={{
                  fontFamily: (theme) => theme.typography.fontFamily,
                  wordBreak: "break-word",
                }}
              >
                {displayJob.job_name || t("common:jobQueue.details.unnamedJob")}
              </Typography>
            </Grid>

            <Grid size={{ xs: 12, md: 6 }}>
              <Typography
                variant="subtitle2"
                sx={{ fontWeight: "bold", color: "text.secondary" }}
              >
                {t("common:jobQueue.details.jobType")}
              </Typography>
              <Typography
                variant="body1"
                sx={{
                  fontFamily: (theme) => theme.typography.fontFamily,
                  wordBreak: "break-word",
                }}
              >
                {displayJob.entity_type ||
                  (displayJob.task_type
                    ? displayJob.task_type.split(".").pop()
                    : t("common:unknown"))}
              </Typography>
            </Grid>

            <Grid size={{ xs: 12, md: 6 }}>
              <Typography
                variant="subtitle2"
                sx={{ fontWeight: "bold", color: "text.secondary" }}
              >
                {t("common:jobQueue.details.lastUpdated")}
              </Typography>
              <Typography
                variant="body1"
                sx={{
                  fontFamily: (theme) => theme.typography.fontFamily,
                  wordBreak: "break-word",
                }}
              >
                {formatDate(displayJob.last_modified || displayJob.last_update)}
              </Typography>
            </Grid>

            <Grid size={{ xs: 12, md: 6 }}>
              <Typography
                variant="subtitle2"
                sx={{ fontWeight: "bold", color: "text.secondary" }}
              >
                {t("common:createdAt")}
              </Typography>
              <Typography
                variant="body1"
                sx={{
                  fontFamily: (theme) => theme.typography.fontFamily,
                  wordBreak: "break-word",
                }}
              >
                {formatDate(displayJob.created_at || displayJob.enqueued_at)}
              </Typography>
            </Grid>

            <Grid size={{ xs: 12, md: 6 }}>
              <Typography
                variant="subtitle2"
                sx={{ fontWeight: "bold", color: "text.secondary" }}
              >
                {t("common:status")}
              </Typography>
              <Typography
                variant="body1"
                sx={{
                  fontFamily: (theme) => theme.typography.fontFamily,
                  wordBreak: "break-word",
                }}
              >
                {getStatusText(displayJob.status, t)}
              </Typography>
            </Grid>

            {displayJob.status === "started" && (
              <Grid size={{ xs: 12 }}>
                <Typography
                  variant="subtitle2"
                  sx={{ fontWeight: "bold", color: "text.secondary" }}
                >
                  {t("common:jobQueue.details.progress")}
                </Typography>
                {displayJob.progress_message && (
                  <Typography variant="body2" color="text.secondary">
                    {displayJob.progress_message}
                  </Typography>
                )}
                <Box display="flex" alignItems="center" gap={2} mt={1}>
                  <Box sx={{ flexGrow: 1 }}>
                    <LinearProgress
                      variant={
                        displayJob.progress != null
                          ? "determinate"
                          : "indeterminate"
                      }
                      value={
                        displayJob.progress != null
                          ? displayJob.progress
                          : undefined
                      }
                      sx={{ height: 6, borderRadius: 1 }}
                    />
                  </Box>
                  {displayJob.progress != null && (
                    <Typography variant="body2" color="text.secondary">
                      {Math.round(displayJob.progress)}%
                    </Typography>
                  )}
                </Box>
              </Grid>
            )}

            {displayJob.error_msg && (
              <Grid size={{ xs: 12 }}>
                <Box mt={2}>
                  <Divider />
                  <Typography
                    variant="subtitle2"
                    sx={{ fontWeight: "bold", color: "error.main", mt: 4 }}
                  >
                    {t("common:jobQueue.details.errorMessage")}
                  </Typography>
                  <Paper
                    variant="outlined"
                    sx={{
                      backgroundColor: (theme) =>
                        theme.palette.mode === "dark"
                          ? theme.palette.grey[900]
                          : theme.palette.grey[100],
                      p: 4,
                      fontSize: "0.875rem",
                      overflow: "auto",
                      maxHeight: "200px",
                    }}
                  >
                    <Typography variant="body1">
                      {displayJob.error_msg}
                    </Typography>
                  </Paper>
                </Box>
              </Grid>
            )}
          </Grid>
        )}
      </DialogContent>

      <DialogActions>
        <Button onClick={onClose} color="primary">
          {t("common:close")}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default JobDetailsDialog;
