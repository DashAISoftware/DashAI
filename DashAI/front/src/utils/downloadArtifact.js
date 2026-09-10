/**
 * Escape one CSV cell: wrap in quotes when it contains a comma, quote, or
 * newline, doubling embedded quotes. null/undefined become an empty cell.
 */
function escapeCsvCell(value) {
  if (value === null || value === undefined) return "";
  const str = typeof value === "object" ? JSON.stringify(value) : String(value);
  if (/[",\r\n]/.test(str)) {
    return `"${str.replace(/"/g, '""')}"`;
  }
  return str;
}

/**
 * Build a CSV string from a table artifact payload ({columns, rows}).
 */
export function artifactToCsv(payload) {
  const { columns = [], rows = [] } = payload ?? {};
  const lines = [columns.map(escapeCsvCell).join(",")];
  rows.forEach((row) => {
    lines.push(row.map(escapeCsvCell).join(","));
  });
  return lines.join("\r\n");
}

/**
 * Trigger a browser download of a Blob under the given filename.
 */
function triggerDownload(blob, filename) {
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

/**
 * Sanitize a title into a safe file basename; fall back to "artifact".
 */
function baseName(title) {
  const cleaned = (title || "artifact")
    .toString()
    .trim()
    .replace(/[^a-z0-9_-]+/gi, "_")
    .replace(/^_+|_+$/g, "");
  return cleaned || "artifact";
}

/**
 * Download an artifact in a format matching its type. For "plotly", pass the
 * rendered plot DOM element in opts.plotEl and the desired image format.
 */
export function downloadArtifact(artifact, opts = {}) {
  const name = baseName(artifact.title);
  switch (artifact.type) {
    case "plotly": {
      if (!opts.plotEl) return;
      const format = opts.format || "png";
      // Plotly is attached to window by react-plotly.js/plotly.js.
      window.Plotly.downloadImage(opts.plotEl, {
        format,
        filename: name,
        height: 800,
        width: 1200,
        scale: 2,
      });
      return;
    }
    case "table": {
      const csv = artifactToCsv(artifact.payload);
      triggerDownload(
        new Blob([csv], { type: "text/csv;charset=utf-8" }),
        `${name}.csv`,
      );
      return;
    }
    case "image": {
      const { data = "", mime = "image/png" } = artifact.payload ?? {};
      const ext = mime.split("/")[1] || "png";
      const byteChars = atob(data);
      const byteNums = new Array(byteChars.length);
      for (let i = 0; i < byteChars.length; i += 1)
        byteNums[i] = byteChars.charCodeAt(i);
      triggerDownload(
        new Blob([new Uint8Array(byteNums)], { type: mime }),
        `${name}.${ext}`,
      );
      return;
    }
    case "text":
    default: {
      const text =
        typeof artifact.payload === "string"
          ? artifact.payload
          : JSON.stringify(artifact.payload, null, 2);
      triggerDownload(
        new Blob([text], { type: "text/plain;charset=utf-8" }),
        `${name}.txt`,
      );
    }
  }
}
