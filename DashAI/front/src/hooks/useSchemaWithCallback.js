import { useEffect, useState } from "react";
import useSchema from "./useSchema";

export default function useSchemaWithCallback({ modelName }, callback) {
  const { defaultValues } = useSchema({ modelName });
  const [prevDefaultValues, setPrevDefaultValues] = useState(defaultValues);

  useEffect(() => {
    if (JSON.stringify(defaultValues) !== JSON.stringify(prevDefaultValues)) {
      callback(defaultValues);
      setPrevDefaultValues(defaultValues);
    }
  }, [defaultValues, prevDefaultValues, callback]);

  return { defaultValues };
}
