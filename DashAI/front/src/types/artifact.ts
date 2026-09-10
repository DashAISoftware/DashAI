/**
 * Typed render artifact returned by explainer plot and explorer results
 * endpoints. Payload shape depends on `type`:
 * - "plotly": JSON string of a plotly figure.
 * - "table": { columns: string[], rows: unknown[][], highlight: {row, column}[] }.
 * - "text": plain string.
 * - "image": { data: base64 string, mime: string }.
 */
export interface IArtifact {
  type: string;
  payload: unknown;
  title: string | null;
  role?: "input" | "explanation";
}
