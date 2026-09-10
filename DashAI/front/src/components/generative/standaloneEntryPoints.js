import MenuBookIcon from "@mui/icons-material/MenuBook";

/**
 * Where each standalone generative task lives in the app, and what it looks
 * like in the module landing.
 *
 * The backend decides *which* tasks are standalone (via each task's
 * `metadata.entry_point`) and what they are *called* (`display_name`,
 * `description`). This map only supplies what the backend has no business
 * knowing: the frontend route and the icon.
 */
export const STANDALONE_ENTRY_POINTS = {
  RAGTask: { route: "/app/generative/rag", Icon: MenuBookIcon },
};

/**
 * Return the route for a standalone task, or null when it has none.
 * @param {string} taskName - The generative task name.
 * @returns {string|null} The route, or null if the task is not standalone.
 */
export function standaloneRouteFor(taskName) {
  return STANDALONE_ENTRY_POINTS[taskName]?.route ?? null;
}

/**
 * Whether a task component is served by its own entry point.
 * @param {object} task - A task component as returned by the components API.
 * @returns {boolean} True when the backend marked it standalone.
 */
export function isStandaloneTask(task) {
  return task?.metadata?.entry_point === "standalone";
}
