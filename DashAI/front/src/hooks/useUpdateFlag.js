import { useEffect } from "react";
import { useSearchParams } from "react-router-dom";

// This hook is used to update a flag in the URL,
// the flag is removed after the updateFunction is called,
// this is useful to trigger a function only once when a flag is set to true
// @param {string} flag - The flag to update
// @param {function} updateFunction - The function to call when the flag is set to true

const useUpdateFlag = ({ flag, updateFunction = null }) => {
  const [searchParams, setSearchParams] = useSearchParams();

  useEffect(() => {
    const urlFlag = searchParams.get(flag);

    if (urlFlag === "true" && Boolean(updateFunction)) {
      updateFunction();
      const { [flag]: _, ...newSearchParams } = searchParams;
      setSearchParams(newSearchParams);
    }
  }, [searchParams, flag, updateFunction]);

  const updateFlag = () => {
    setSearchParams({ ...searchParams, [flag]: true });
  };

  return { updateFlag };
};

export default useUpdateFlag;
