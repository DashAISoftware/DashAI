import { useEffect, useState } from "react";
import { getComponents } from "../api/component";

/*
 * This hook is used to get the parent models of a model
 * @param {string} parent - The parent model
 */

export default function useModelParents({ parent }) {
  const [models, setModels] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const getModels = async () => {
      try {
        setLoading(true);
        const result = await getComponents({
          componentParent: parent,
        });

        setModels(result);
      } catch (error) {
        console.log(error);
      } finally {
        setLoading(false);
      }
    };

    if (parent) {
      getModels();
    }
  }, [parent]);

  return { models, loading };
}
