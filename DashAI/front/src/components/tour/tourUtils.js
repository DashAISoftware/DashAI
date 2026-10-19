import { useEffect } from "react";

const selectorFor = (name) => `[data-tour="${name}"]`;

/**
 * Whether the running tour is currently on the step that targets
 * `[data-tour="name"]`. Guards asynchronous advances (search results,
 * downloads) so they only move the tour from the step they belong to.
 */
export const isTourAtTarget = (tourContext, name) =>
  !!tourContext?.run &&
  tourContext.steps?.[tourContext.stepIndex]?.target === selectorFor(name);

/** Index of the first step that targets `[data-tour="name"]`, or -1. */
export const tourStepIndexOf = (tourContext, name) =>
  tourContext?.steps?.findIndex((s) => s.target === selectorFor(name)) ?? -1;

/**
 * Call `fn` as soon as `selector` matches an element in the DOM.
 * Returns a function that cancels the wait.
 */
export const runWhenPresent = (selector, fn) => {
  if (document.querySelector(selector)) {
    fn();
    return () => {};
  }
  const observer = new MutationObserver(() => {
    if (document.querySelector(selector)) {
      observer.disconnect();
      fn();
    }
  });
  observer.observe(document.body, { childList: true, subtree: true });
  return () => observer.disconnect();
};

/** Jump to the first step targeting `[data-tour="name"]` once it renders. */
export const goToTourTarget = (tourContext, name) => {
  const index = tourStepIndexOf(tourContext, name);
  if (index < 0) return () => {};
  return runWhenPresent(selectorFor(name), () => tourContext.goToStep(index));
};

/**
 * Keep a multi-screen tour in step with the screen the user is on.
 *
 * Steps may declare a `stage`; when the running step belongs to a stage other
 * than `stage` (the user moved forward or back, or relaunched the tour from a
 * later screen), the tour jumps to the first step of `stage` once its target
 * is rendered. Steps without a `stage` (e.g. a centered intro) are left alone.
 */
export const useTourStageSync = (tourContext, stage) => {
  const run = !!tourContext?.run;
  const stepIndex = tourContext?.stepIndex;

  useEffect(() => {
    if (!run) return undefined;
    const steps = tourContext.steps;
    const current = steps[stepIndex];
    if (current?.stage == null || current.stage === stage) return undefined;
    const index = steps.findIndex((s) => s.stage === stage);
    if (index < 0) return undefined;
    return runWhenPresent(steps[index].target, () =>
      tourContext.goToStep(index),
    );
  }, [run, stepIndex, stage]);
};
