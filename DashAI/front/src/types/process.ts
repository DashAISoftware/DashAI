/**
 * Live RAG pipeline stage reported on a process's `progress` field while the
 * answer is being produced. The backend advances it through these values and
 * resets the field to null once the process finishes or errors.
 */
export type RAGProgressStage = "transforming" | "retrieving" | "generating";

export type RAGProgressPayload = {
  stage?: RAGProgressStage;
  queries?: string[];
};

export interface IProcess {
  id: string;
  created: Date;
  last_modified: Date;
  start_time: Date | null;
  status: number;
  session_id: number;
  delivery_time: Date;
  end_time: Date | null;
  input: IDataProcess[];
  output: IDataProcess[];
  progress?: RAGProgressPayload | null;
}

export interface IDataProcess {
  id: number;
  process_id: number;
  data: string;
  data_type: string;
  is_input: boolean;
}
