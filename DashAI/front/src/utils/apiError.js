/**
 * Extract the message the backend sent with a failed request.
 *
 * FastAPI puts the explanation in `detail`, which is usually a string but is an
 * object for richer errors (the duplicate-document 409, for instance). Without
 * this, a caller that only logs the error leaves the user staring at a silent
 * failure even though the backend said exactly what was wrong.
 *
 * @param {unknown} error - The rejected value, typically an axios error.
 * @param {string} [fallback=""] - Returned when no message can be recovered.
 * @returns {string} A human-readable reason, or the fallback.
 */
export function getApiErrorMessage(error, fallback = "") {
  const detail = error?.response?.data?.detail;

  if (typeof detail === "string" && detail.trim()) return detail;

  // Object details carry their own nested message (e.g. the 409 duplicate).
  if (detail && typeof detail === "object") {
    if (typeof detail.detail === "string" && detail.detail.trim()) {
      return detail.detail;
    }
    // Pydantic validation errors arrive as a list of {loc, msg, type}.
    if (Array.isArray(detail)) {
      const messages = detail
        .map((entry) => entry?.msg)
        .filter((msg) => typeof msg === "string" && msg.trim());
      if (messages.length) return messages.join("; ");
    }
  }

  if (typeof error?.message === "string" && error.message.trim()) {
    return error.message;
  }

  return fallback;
}

/**
 * Like getApiErrorMessage, for requests made with responseType "blob".
 *
 * A failed download still arrives as a Blob, so the JSON with `detail` has to
 * be read out of it before the message can be found.
 *
 * @param {unknown} error - The rejected value, typically an axios error.
 * @param {string} [fallback=""] - Returned when no message can be recovered.
 * @returns {Promise<string>} A human-readable reason, or the fallback.
 */
export async function getApiErrorMessageAsync(error, fallback = "") {
  const data = error?.response?.data;
  if (typeof Blob !== "undefined" && data instanceof Blob) {
    try {
      const parsed = JSON.parse(await data.text());
      return getApiErrorMessage(
        { ...error, response: { ...error.response, data: parsed } },
        fallback,
      );
    } catch {
      return getApiErrorMessage({ message: error?.message }, fallback);
    }
  }
  return getApiErrorMessage(error, fallback);
}
