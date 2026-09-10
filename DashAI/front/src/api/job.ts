import api from "./api";

export const isQueueEmpty = async (): Promise<boolean> => {
  const response = await api.get<{ is_empty: boolean }>("/v1/job/is_empty");
  return response.data.is_empty;
};

export const getJobs = async (): Promise<object> => {
  const response = await api.get<object>("/v1/job/");
  return response.data;
};

export const getJobChanges = async (
  since: string,
): Promise<{
  jobs: any[];
  cursor: string;
  server_now: string;
  queue_empty: boolean;
  recently_completed: boolean;
}> => {
  const response = await api.get<any>("/v1/job/changes", {
    params: { since },
  });
  return response.data;
};

export const getJobDetails = async (jobId: string): Promise<object> => {
  const response = await api.get<object>(`/v1/job/${jobId}/details`);
  return response.data;
};

export const getJobStatus = async (jobId: string): Promise<any> => {
  const response = await api.get<any>(`/v1/job/status/${jobId}`);
  return response.data;
};

export const enqueueRunnerJob = async (runId: number): Promise<object> => {
  const data = {
    job_type: "ModelJob",
    kwargs: { run_id: runId },
  };
  const formData = new FormData();
  formData.append("job_type", data.job_type);
  formData.append("kwargs", JSON.stringify(data.kwargs));
  const response = await api.post<object>("/v1/job/", formData, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
  });
  return response.data;
};

export const enqueueReportJob = async (reportId: number): Promise<object> => {
  const formData = new FormData();
  formData.append("job_type", "ReportJob");
  formData.append("kwargs", JSON.stringify({ report_id: reportId }));
  const response = await api.post<object>("/v1/job/", formData, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
  });
  return response.data;
};

export const enqueueDatasetJob = async (
  dataset_id: number,
  file: File | null,
  url: string,
  params: object,
  notebook_id: number | null = null,
): Promise<object> => {
  const formData = new FormData();
  const kwargs = {
    dataset_id: dataset_id,
    notebook_id: notebook_id,
    url: url,
    params: params,
  };

  formData.append("job_type", "DatasetJob");
  formData.append("kwargs", JSON.stringify(kwargs));
  if (file) formData.append("file", file);

  const response = await api.post<object>("/v1/job/", formData, {
    headers: {
      "Content-Type": "multipart/form-data",
      filename: file ? encodeURIComponent(file.name) : "",
    },
  });
  return response.data;
};

export const enqueueExplainerJob = async (
  explainerId: number,
  scope: string,
  manualInputData?: object[],
): Promise<object> => {
  const formData = new FormData();

  // When the local explainer explains manually-entered inputs, the rows travel
  // in the job kwargs (like manual predictions). File values are swapped for a
  // placeholder key and the File is appended separately so the job endpoint can
  // reattach it.
  const kwargs: Record<string, unknown> = {
    explainer_id: explainerId,
    explainer_scope: scope,
  };

  if (manualInputData) {
    kwargs.manual_input_data = manualInputData.map((obj, i) => {
      const cleanObj: Record<string, unknown> = {};
      Object.entries(obj).forEach(([key, value]) => {
        if (value instanceof File) {
          const fieldName = `file_${i}_${key}`;
          formData.append(fieldName, value);
          cleanObj[key] = fieldName;
        } else {
          cleanObj[key] = value;
        }
      });
      return cleanObj;
    });
  }

  formData.append("job_type", "ExplainerJob");
  formData.append("kwargs", JSON.stringify(kwargs));

  const response = await api.post<object>("/v1/job/", formData, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
  });
  return response.data;
};

export const enqueueExplorerJob = async (
  explorerId: number,
): Promise<object> => {
  const formData = new FormData();
  const kwargs = {
    explorer_id: explorerId,
  };

  formData.append("job_type", "ExplorerJob");
  formData.append("stop_when_queue_empties", JSON.stringify(true));
  formData.append("kwargs", JSON.stringify(kwargs));

  const response = await api.post<object>("/v1/job/", formData, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
  });
  return response.data;
};

export const enqueuePredictionJob = async (
  prediction_id: number,
  manual_input_data?: object[],
): Promise<object> => {
  const formData = new FormData();

  const simpleManualData = manual_input_data?.map((obj, i) => {
    const cleanObj: any = {};
    Object.entries(obj).forEach(([key, value]) => {
      if (value instanceof File) {
        const fieldName = `file_${i}_${key}`;
        formData.append(fieldName, value);
        cleanObj[key] = fieldName;
      } else {
        cleanObj[key] = value;
      }
    });
    return cleanObj;
  });

  const data = {
    job_type: "PredictJob",
    kwargs: { prediction_id, manual_input_data: simpleManualData },
  };

  formData.append("job_type", data.job_type);
  formData.append("kwargs", JSON.stringify(data.kwargs));

  const response = await api.post<object>("/v1/job/", formData, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
  });
  return response.data;
};

export const enqueueGenerativeProcessJob = async (
  processId: number,
): Promise<object> => {
  const data = {
    job_type: "GenerativeJob",
    kwargs: { generative_process_id: processId },
  };

  const formData = new FormData();
  formData.append("job_type", data.job_type);
  formData.append("kwargs", JSON.stringify(data.kwargs));

  const response = await api.post<object>("/v1/job/", formData, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
  });
  return response.data;
};

export const enqueueConverterJob = async (
  converterId: number,
): Promise<object> => {
  const data = {
    job_type: "ConverterJob",
    kwargs: {
      converter_id: converterId,
    },
    stop_when_queue_empties: true,
  };

  const formData = new FormData();
  formData.append("job_type", data.job_type);
  formData.append(
    "stop_when_queue_empties",
    JSON.stringify(data.stop_when_queue_empties),
  );
  formData.append("kwargs", JSON.stringify(data.kwargs));

  const response = await api.post<object>("/v1/job/", formData, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
  });
  return response.data;
};

export const startJobQueue = async (
  stopWhenQueueEmpties?: boolean,
): Promise<void> => {
  return;
};

export const deleteJob = async (jobId: string): Promise<void> => {
  await api.delete(`/v1/job/${jobId}`);
};

export const deleteAllJobs = async (): Promise<{ deleted: number }> => {
  const response = await api.delete<{ deleted: number }>("/v1/job/all");
  return response.data;
};

export const enqueuePipelineJob = async (
  pipelineId: number,
): Promise<object> => {
  const data = {
    job_type: "PipelineJob",
    kwargs: { id: pipelineId },
  };

  const formData = new FormData();
  formData.append("job_type", data.job_type);
  formData.append("kwargs", JSON.stringify(data.kwargs));

  const response = await api.post<object>("/v1/job/", formData, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
  });
  return response.data;
};

export const enqueueDatafileJob = async (
  datafileId: number,
  sourceName: string,
  datasetSourceId: string,
): Promise<{ id: string }> => {
  const formData = new FormData();
  formData.append("job_type", "DatafileJob");
  formData.append(
    "kwargs",
    JSON.stringify({
      kwargs: {
        datafile_id: datafileId,
        source_name: sourceName,
        dataset_source_id: datasetSourceId,
      },
    }),
  );
  const response = await api.post<{ id: string }>("/v1/job/", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return response.data;
};
