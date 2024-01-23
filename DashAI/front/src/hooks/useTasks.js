import { useSnackbar } from "notistack";
import { useEffect, useState } from "react";
import { getComponents as getComponentsRequest } from "../api/component";

export default function useTasks({ onSuccess }) {
  const { enqueueSnackbar } = useSnackbar();
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const getTasks = async () => {
      setLoading(true);
      try {
        const tasks = await getComponentsRequest({ selectTypes: ["Task"] });
        setTasks(tasks);
        onSuccess && onSuccess(tasks);
      } catch (error) {
        enqueueSnackbar("Error while trying to obtain available tasks");
        if (error.response) {
          console.error("Response error:", error.message);
        } else if (error.request) {
          console.error("Request error", error.request);
        } else {
          console.error("Unknown Error", error.message);
        }
      } finally {
        setLoading(false);
      }
    };

    getTasks();
  }, []);

  return { tasks, loading };
}
