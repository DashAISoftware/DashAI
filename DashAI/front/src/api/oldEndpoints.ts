import api from "./api";

export const getSchema = async(schemaType:string, objName:string): Promise<object> => {
    const response = await api.get<object>(`/v0/select/${schemaType}/${objName}`);
    return response.data;
}

export const getChildren = async(parent:string): Promise<object> => {
    const response = await api.get<object>(`/v0/getChildren/${parent}`)
    return response.data;
}

export const getModelSchema = async(modelName:string): Promise<object> => {
    const response = await api.get<object>(`/v0/selectModel/${modelName}`)
    return response.data;
}

// The endpoint calls below are not tested, because they correspond to parts of the front that are not implemented yet.
export const submitParameters = async(modelName:string, params: string): Promise<object> => {
    const response = await api.post<object>(`/v0/selectedParameters/${modelName}`, params)
    return response.data;
}

export const runExperiment = async(sessionId: number): Promise<object> => {
    const response = await api.post<object>(`/v0/experiment/run/${sessionId}`);
    return response.data;
}

export const getResults = async(sessionId: number): Promise<object> => {
    const response = await api.get<object>(`/v0/experiment/results/${sessionId}`);
    return response.data;
}

export const getPrediction = async(sessionId: number, executionId:number, input:string): Promise<object> => {
    const response = await api.get<object>(`/v0/play/${sessionId}/${executionId}/${input}`);
    return response.data;
}



