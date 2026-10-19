import { useState, useCallback, useEffect, useRef } from "react";
import { getToursAutostart } from "../api/appConfig";

const TOUR_STORAGE_KEY = "dashai_tours_completed";
const TOUR_HANDOFF_KEY = "dashai_tour_handoff";
const TARGET_POLL_MS = 200;
const TARGET_WAIT_MS = 8000;

const isTargetVisible = (selector) => {
  const element = document.querySelector(selector);
  if (!element) return false;
  for (
    let node = element;
    node && node !== document.body;
    node = node.parentElement
  ) {
    const { display, visibility } = getComputedStyle(node);
    if (display === "none" || visibility === "hidden") return false;
  }
  return true;
};

const takeHandoff = (tourKey) => {
  const handoffs = JSON.parse(sessionStorage.getItem(TOUR_HANDOFF_KEY) || "{}");
  if (!(tourKey in handoffs)) return null;
  const step = handoffs[tourKey];
  delete handoffs[tourKey];
  sessionStorage.setItem(TOUR_HANDOFF_KEY, JSON.stringify(handoffs));
  return step;
};

export const useTour = (tourKey) => {
  const [run, setRun] = useState(false);
  const [stepIndex, setStepIndex] = useState(0);
  const runRef = useRef(false);
  const missingRef = useRef({ index: null, since: 0, timer: null });

  useEffect(() => {
    runRef.current = run;
  }, [run]);

  const clearMissingWatch = useCallback(() => {
    clearInterval(missingRef.current.timer);
    missingRef.current = { index: null, since: 0, timer: null };
  }, []);

  useEffect(() => clearMissingWatch, [clearMissingWatch]);

  useEffect(() => {
    clearMissingWatch();
    setRun(false);
    setStepIndex(0);

    let cancelled = false;
    const timer = setTimeout(() => {
      // A handoff continues a tour the user is already following on another
      // page, so it resumes even when auto-start is off.
      const handoffStep = takeHandoff(tourKey);
      if (handoffStep !== null) {
        setStepIndex(handoffStep);
        setRun(true);
        return;
      }
      const completedTours = JSON.parse(
        localStorage.getItem(TOUR_STORAGE_KEY) || "{}",
      );
      if (completedTours[tourKey]) return;
      // Auto-start can be turned off app-wide (`--no-tours`, e.g. for demos);
      // the navbar help button still starts tours on demand.
      getToursAutostart().then((enabled) => {
        if (!cancelled && enabled) setRun(true);
      });
    }, 500);
    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
  }, [tourKey, clearMissingWatch]);

  const startTour = useCallback(() => {
    clearMissingWatch();
    setStepIndex(0);
    setRun(true);
  }, [clearMissingWatch]);

  const stopTour = useCallback(() => {
    clearMissingWatch();
    setRun(false);
  }, [clearMissingWatch]);

  const resetTour = useCallback(() => {
    clearMissingWatch();
    setStepIndex(0);
    setRun(false);
  }, [clearMissingWatch]);

  const goToStep = useCallback((step) => {
    setStepIndex(step);
  }, []);

  const resumeAtStep = useCallback((step) => {
    setRun(false);
    setTimeout(() => {
      setStepIndex(step);
      setRun(true);
    }, 80);
  }, []);

  const nextStep = useCallback(() => {
    setStepIndex((prevIndex) => {
      return prevIndex + 1;
    });
  }, [stepIndex]);

  const markTourAsCompleted = useCallback(() => {
    const completedTours = JSON.parse(
      localStorage.getItem(TOUR_STORAGE_KEY) || "{}",
    );
    completedTours[tourKey] = true;
    localStorage.setItem(TOUR_STORAGE_KEY, JSON.stringify(completedTours));
  }, [tourKey]);

  const handoffTour = useCallback(
    (step) => {
      const handoffs = JSON.parse(
        sessionStorage.getItem(TOUR_HANDOFF_KEY) || "{}",
      );
      handoffs[tourKey] = step;
      sessionStorage.setItem(TOUR_HANDOFF_KEY, JSON.stringify(handoffs));
    },
    [tourKey],
  );

  const completeTour = useCallback(() => {
    clearMissingWatch();
    markTourAsCompleted();
    setRun(false);
  }, [clearMissingWatch, markTourAsCompleted]);

  const resetAllTours = useCallback(() => {
    localStorage.removeItem(TOUR_STORAGE_KEY);
  }, []);

  const watchMissingTarget = useCallback(
    (target, index, action) => {
      const watch = missingRef.current;
      clearInterval(watch.timer);
      const since = watch.index === index ? watch.since : Date.now();
      const timer = setInterval(() => {
        if (!runRef.current) {
          clearMissingWatch();
        } else if (isTargetVisible(target)) {
          clearInterval(timer);
          missingRef.current.timer = null;
          resumeAtStep(index);
        } else if (Date.now() - since >= TARGET_WAIT_MS) {
          clearMissingWatch();
          setStepIndex(action === "prev" ? Math.max(index - 1, 0) : index + 1);
        }
      }, TARGET_POLL_MS);
      missingRef.current = { index, since, timer };
    },
    [clearMissingWatch, resumeAtStep],
  );

  const handleJoyrideCallback = useCallback(
    (data) => {
      const { action, status, index, type, step } = data;
      if (type === "error:target_not_found") {
        watchMissingTarget(step.target, index, action);
        return;
      }

      if (type === "tooltip") {
        clearMissingWatch();
      }

      if (status === "finished" || status === "skipped") {
        markTourAsCompleted();
        setRun(false);
        return;
      }

      if (type === "step:after") {
        if (action === "next" || action === "start") {
          setStepIndex(index + 1);
        } else if (action === "prev") {
          setStepIndex(Math.max(index - 1, 0));
        } else if (action === "close") {
          setRun(false);
          markTourAsCompleted();
        }
      }
    },
    [markTourAsCompleted, watchMissingTarget, clearMissingWatch],
  );

  return {
    run,
    stepIndex,
    startTour,
    stopTour,
    completeTour,
    handoffTour,
    resetTour,
    resetAllTours,
    handleJoyrideCallback,
    goToStep,
    nextStep,
    resumeAtStep,
    markTourAsCompleted,
  };
};
