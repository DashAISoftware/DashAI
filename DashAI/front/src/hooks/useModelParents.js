import { useEffect, useState } from "react";
import { getComponents } from "../api/component";

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
