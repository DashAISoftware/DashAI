import api from "./api";

export interface IReport {
  id: number;
  run_id: number;
  report_name: string;
  parameters: object;
  artifacts_path: string | null;
  status: number;
  created: string;
}

export const getReports = async (runId: number): Promise<IReport[]> => {
  const response = await api.get<IReport[]>("/v1/report/", {
    params: { run_id: runId },
  });
  return response.data;
};

export const getReportArtifacts = async (reportId: number): Promise<any[]> => {
  const response = await api.get<any[]>(`/v1/report/${reportId}/artifacts`);
  return response.data;
};

export const createReport = async (
  runId: number,
  reportName: string,
  parameters: object = {},
): Promise<IReport> => {
  const response = await api.post<IReport>("/v1/report/", {
    run_id: runId,
    report_name: reportName,
    parameters,
  });
  return response.data;
};

export const deleteReport = async (reportId: number): Promise<void> => {
  await api.delete(`/v1/report/${reportId}`);
};

/** Persist an edited plotly figure so it survives a reload. */
export const saveReportPlotOverride = async (
  reportId: number,
  index: number,
  figure: unknown,
): Promise<void> => {
  await api.put(`/v1/report/${reportId}/override`, { index, figure });
};

/** Drop a stored edit so the computed figure comes back. */
export const deleteReportPlotOverride = async (
  reportId: number,
  index: number,
): Promise<void> => {
  await api.delete(`/v1/report/${reportId}/override/${index}`);
};
