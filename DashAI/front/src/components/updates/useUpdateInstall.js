import { useCallback, useEffect, useState } from "react";
import { getJobs } from "../../api/job";
import {
  getUpdateDownloadStatus,
  installUpdate,
  startUpdateDownload,
} from "../../api/system";
import { startJobPolling, subscribeJobs } from "../../utils/jobPoller";

// UpdateDownloadJob names itself "Download update: <file name>".
const DOWNLOAD_JOB_PREFIX = "Download update:";
const ACTIVE_JOB_STATUSES = ["not_started", "started"];

/**
 * Drive the download and install of an update from the updates dialog.
 *
 * The phase is one of:
 * - "idle": nothing in progress (the file may or may not be downloaded yet)
 * - "downloading": the download job is running
 * - "confirm": jobs are running and the user must confirm stopping them
 * - "installing": the install request is in flight
 * - "installed": the backend accepted the install and is closing dashAI
 * - "error": the download or the install failed (see `error`)
 *
 * @param {boolean} active Whether this install can be updated from a file and
 *   the dialog is open. Status is only fetched while active.
 */
export default function useUpdateInstall(active) {
  const [status, setStatus] = useState(null);
  const [phase, setPhase] = useState("idle");
  const [progress, setProgress] = useState(null);
  const [jobId, setJobId] = useState(null);
  const [error, setError] = useState(null);
  const [installedChannel, setInstalledChannel] = useState(null);

  const refresh = useCallback(async () => {
    try {
      const data = await getUpdateDownloadStatus();
      setStatus(data);
      return data;
    } catch {
      setStatus(null);
      return null;
    }
  }, []);

  const watch = useCallback(
    (id) => {
      setJobId(id);
      setPhase("downloading");
      startJobPolling(
        id,
        async () => {
          setJobId(null);
          setPhase("idle");
          await refresh();
        },
        (job) => {
          setJobId(null);
          if (job?.status === "cancelled") {
            setPhase("idle");
          } else {
            setPhase("error");
            setError({ kind: "download" });
          }
          refresh();
        },
      );
    },
    [refresh],
  );

  // Load the status when the dialog opens, and pick up a download that is
  // still running (the dialog was closed, or the page reloaded, meanwhile).
  useEffect(() => {
    if (!active) return;
    refresh();
    if (jobId) return;
    getJobs()
      .then((jobs) => {
        const running = (Array.isArray(jobs) ? jobs : []).find(
          (job) =>
            job.job_name?.startsWith(DOWNLOAD_JOB_PREFIX) &&
            ACTIVE_JOB_STATUSES.includes(job.status),
        );
        if (running) {
          setProgress(running.progress ?? null);
          watch(running.id);
        }
      })
      .catch(() => {});
    // jobId is deliberately not a dependency: it is only read on open to
    // avoid watching the same job twice, and watch() keeps it up to date.
  }, [active, refresh, watch]);

  useEffect(() => {
    if (!jobId) return undefined;
    return subscribeJobs((jobs) => {
      const job = jobs.find((item) => item.id === jobId);
      if (job && job.progress != null) setProgress(job.progress);
    });
  }, [jobId]);

  const startDownload = useCallback(async () => {
    setError(null);
    setProgress(0);
    try {
      const { id } = await startUpdateDownload();
      watch(id);
    } catch {
      setPhase("error");
      setError({ kind: "download" });
    }
  }, [watch]);

  const install = useCallback(
    async (stopRunningJobs = false) => {
      setError(null);
      const current = await refresh();
      if (!stopRunningJobs && current?.jobs_running) {
        setPhase("confirm");
        return;
      }
      setPhase("installing");
      try {
        const { channel } = await installUpdate(stopRunningJobs);
        setInstalledChannel(channel);
        setPhase("installed");
      } catch (e) {
        setPhase("error");
        setError({ kind: "install", detail: e?.response?.data?.detail });
      }
    },
    [refresh],
  );

  const cancelConfirm = useCallback(() => setPhase("idle"), []);

  return {
    status,
    phase,
    progress,
    error,
    installedChannel,
    startDownload,
    install,
    cancelConfirm,
  };
}
