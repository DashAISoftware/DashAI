import { useState, useEffect } from "react";

/**
 * This is a hook to debounce a value
 * @param {any} value - The value to debounce
 * @param {number} delay - The delay to wait before updating the value
 */

function useDebounce(value, delay = 500) {
  const [debouncedValue, setDebouncedValue] = useState(value);

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => {
      clearTimeout(handler);
    };
  }, [value, delay]);

  return debouncedValue;
}

export default useDebounce;
