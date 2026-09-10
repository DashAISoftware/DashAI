import { useGenerative } from "../../components/generative/GenerativeContext";

/**
 * The friendly, localized name of a generative task.
 *
 * Task names come from the backend already translated, so a view scoped to one
 * task can label itself without carrying a string of its own. Falls back to the
 * task name while the task list is still loading.
 *
 * @param {string} taskName - The task's registry name (e.g. "RAGTask").
 * @returns {string} The task's display name, or the given name as a fallback.
 */
export function useTaskDisplayName(taskName) {
  const { tasks } = useGenerative() ?? {};
  const task = (tasks ?? []).find((candidate) => candidate.name === taskName);
  return task?.display_name || taskName;
}
