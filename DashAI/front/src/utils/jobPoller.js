import { getJobs, getJobStatus, isQueueEmpty, getJobChanges } from "../api/job";

const POLL_INTERVAL = 1000; // Default polling interval (2 seconds)

// Central state
const state = {
  active: false, // Is polling currently active
  intervalId: null, // ID of the main polling interval
  subscribers: new Set(), // Components listening for job updates
  jobWatchers: new Map(), // Map of individual jobs being tracked (jobId -> {intervalId, onSuccess, onError})
  lastFetchTime: null, // Last successful fetch time
  lastCursor: null, // Last cursor for job changes
  lastCompletionTime: null, // Last time a job was completed
};

/**
 * Start the global job polling system
 */
export function startJobPoller() {
  if (state.active) return;
  state.active = true;

  // Clear any existing interval
  if (state.intervalId) {
    clearInterval(state.intervalId);
  }

  // Poll immediately and then at regular intervals
  pollJobs();
  state.intervalId = setInterval(pollJobs, POLL_INTERVAL);
}

/**
 * Stop the global job polling system
 */
export function stopJobPoller() {
  if (!state.active) return;

  if (state.intervalId) {
    clearInterval(state.intervalId);
    state.intervalId = null;
  }
  state.active = false;
}

/**
 * Check if there are any active jobs in the list
 */
function hasActiveJobs(jobs) {
  return jobs.some(
    (job) => job.status === "not_started" || job.status === "started",
  );
}

/**
 * Main polling function that checks all jobs
 */
async function pollJobs() {
  try {
    if (state.subscribers.size === 0 && state.jobWatchers.size === 0) {
      const isEmpty = await isQueueEmpty();
      if (isEmpty) {
        stopJobPoller();
        return;
      }
    }

    const changeData = await getJobChanges(state.lastCursor);
    state.lastCursor = changeData.cursor;
    state.lastFetchTime = new Date();

    const jobsToProcess = changeData.jobs || [];

    const activeJobsExist = hasActiveJobs(jobsToProcess);
    for (const subscriber of state.subscribers) {
      try {
        subscriber(jobsToProcess);
      } catch (error) {
        console.error("[JobPoller] Subscriber error:", error);
      }
    }

    for (const [jobId, watcher] of state.jobWatchers.entries()) {
      const job = jobsToProcess.find((j) => j.id === jobId);

      if (job) {
        if (job.status === "finished") {
          if (watcher.onSuccess) watcher.onSuccess(job);
          stopJobPolling(jobId);
        } else if (job.status === "error") {
          if (watcher.onError) watcher.onError(job);
          stopJobPolling(jobId);
        }
      }
    }

    if (changeData.recently_completed) {
      state.lastCompletionTime = Date.now();
    }

    const MIN_POLLING_AFTER_COMPLETION = 5000; // 5 seconds
    const timePassedSinceCompletion = state.lastCompletionTime
      ? Date.now() - state.lastCompletionTime
      : Infinity;

    // When the queue is truly empty and the grace period has elapsed (or no
    // completion was ever detected), resolve any orphaned watchers (jobs deleted
    // from the queue that will never appear in incremental changes) using the
    // authoritative state from getJobs(). Subscribers are NOT flushed here —
    // they receive incremental updates during the grace period via normal polling,
    // and sending a full snapshot would leave stale deleted-job entries in their
    // state. If getJobs() fails, leave watchers in place and retry next poll.
    if (
      changeData.queue_empty &&
      !changeData.recently_completed &&
      timePassedSinceCompletion > MIN_POLLING_AFTER_COMPLETION
    ) {
      if (state.jobWatchers.size === 0) {
        stopJobPoller();
        return;
      }
      try {
        const allJobs = await getJobs();
        for (const [jobId, watcher] of [...state.jobWatchers.entries()]) {
          const job = allJobs.find((j) => j.id === jobId);
          if (job?.status === "finished") {
            if (watcher.onSuccess) watcher.onSuccess(job);
            stopJobPolling(jobId);
          } else if (job?.status === "error") {
            if (watcher.onError) watcher.onError(job);
            stopJobPolling(jobId);
          } else if (!job) {
            // The job vanished from the queue entirely; treat it as failed.
            if (watcher.onError)
              watcher.onError({ id: jobId, status: "deleted" });
            stopJobPolling(jobId);
          }
          // A job still pending or running is left watched and rechecked on the
          // next poll, so a freshly queued job is never reported as an error
          // just because the queue briefly looked empty.
        }
        if (state.jobWatchers.size === 0) {
          stopJobPoller();
        }
        return;
      } catch (e) {
        console.error("[JobPoller] Final flush failed, will retry:", e);
        // Fall through — watchers stay intact, next poll retries the flush
      }
    }

    if (
      !activeJobsExist &&
      state.jobWatchers.size === 0 &&
      !changeData.recently_completed &&
      timePassedSinceCompletion > MIN_POLLING_AFTER_COMPLETION
    ) {
      stopJobPoller();
      return;
    }
  } catch (error) {
    console.error("[JobPoller] Error polling jobs:", error);
  }
}

/**
 * Start polling for a specific job
 * @param {string} jobId - ID of the job to watch
 * @param {Function} onSuccess - Callback when job completes successfully
 * @param {Function} onError - Callback when job fails
 */
export function startJobPolling(jobId, onSuccess, onError) {
  if (!jobId) return;

  // Stop existing polling for this job if any
  stopJobPolling(jobId);

  // Store the watcher - the global polling system will handle callbacks
  state.jobWatchers.set(jobId, {
    intervalId: null,
    onSuccess,
    onError,
  });

  // Make sure global polling is active
  if (!state.active) {
    startJobPoller();
  }
}

/**
 * Stop polling for a specific job
 */
export function stopJobPolling(jobId) {
  if (!state.jobWatchers.has(jobId)) return;

  const watcher = state.jobWatchers.get(jobId);
  if (watcher.intervalId) {
    clearInterval(watcher.intervalId);
  }

  state.jobWatchers.delete(jobId);
}

/**
 * Subscribe to updates for all jobs
 */
export function subscribeJobs(callback) {
  if (typeof callback !== "function") return () => {};

  state.subscribers.add(callback);

  // Make sure polling is active
  if (!state.active) {
    startJobPoller();
  }

  return () => {
    state.subscribers.delete(callback);

    // If no more subscribers and no job watchers, stop polling
    if (state.subscribers.size === 0 && state.jobWatchers.size === 0) {
      stopJobPoller();
    }
  };
}

/**
 * Force an immediate refresh of job status
 */
export function forceRefreshNow() {
  if (!state.active) {
    startJobPoller();
  } else {
    pollJobs();
  }
}

/**
 * Check if the queue has jobs and start polling if needed
 */
export async function checkQueueAndMaybeStartPolling() {
  try {
    const isEmpty = await isQueueEmpty();

    if (!isEmpty) {
      // Check if there are active jobs before starting polling
      const jobs = await getJobs();
      const activeJobsExist = hasActiveJobs(jobs);

      if (activeJobsExist && !state.active) {
        startJobPoller();
      }

      return activeJobsExist;
    }
    return false;
  } catch (error) {
    console.error("[JobPoller] Error checking queue:", error);
    return false;
  }
}

/**
 * Clean up all resources (call on app shutdown or navigation)
 */
export function cleanupJobPoller() {
  // Clear main interval
  if (state.intervalId) {
    clearInterval(state.intervalId);
    state.intervalId = null;
  }

  // Clear all job watcher intervals
  for (const [jobId, watcher] of state.jobWatchers.entries()) {
    if (watcher.intervalId) {
      clearInterval(watcher.intervalId);
    }
  }

  // Reset state
  state.active = false;
  state.jobWatchers.clear();
  state.subscribers.clear();
  state.lastFetchTime = null;
}
