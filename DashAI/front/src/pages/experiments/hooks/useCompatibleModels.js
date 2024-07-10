import { useSnackbar } from "notistack";
import { useEffect, useState } from "react";
import { getComponents as getComponentsRequest } from "../../../api/component";

/*
 * Custom hook to fetch compatible models from the backend
 * @param {string} relatedComponent - id of the related component
 */

export default function useCompatibleModels({ relatedComponent }) {
  const [compatibleModels, setCompatibleModels] = useState([]);
  const { enqueueSnackbar } = useSnackbar();

  // in mount, fetches the compatible models with the previously selected task
  useEffect(() => {
    const getCompatibleModels = async () => {
      try {
        const models = await getComponentsRequest({
          selectTypes: ["Model"],
          relatedComponent,
        });
        setCompatibleModels(models);
      } catch (error) {
        enqueueSnackbar("Error while trying to obtain compatible models");
        if (error.response) {
          console.error("Response error:", error.message);
        } else if (error.request) {
          console.error("Request error", error.request);
        } else {
          console.error("Unknown Error", error.message);
        }
      }
    };

    getCompatibleModels();
  }, [relatedComponent]);

  return { compatibleModels };
}
