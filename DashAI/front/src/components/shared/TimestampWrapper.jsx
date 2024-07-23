import React from "react";
import { useTimestamp } from "../../hooks/useTimestamp";

const TimestampWrapper = ({ children, eventName }) => {
  const { handleClick } = useTimestamp({ eventName });

  if (!children) {
    return null;
  }

  if (!eventName) {
    return children;
  }

  return <div onClick={handleClick}>{children}</div>;
};

export default TimestampWrapper;
