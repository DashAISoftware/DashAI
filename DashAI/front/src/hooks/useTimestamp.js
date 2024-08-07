import { useState, useEffect } from "react";

const STORAGE_KEY = "clickEvents";

export const useTimestamp = ({ eventName }) => {
  const [events, setEvents] = useState(() => {
    const storedEvents = localStorage.getItem(STORAGE_KEY);
    return storedEvents ? JSON.parse(storedEvents) : [];
  });

  const handleClick = () => {
    const newEvent = { eventName, timestamp: new Date().getTime() };
    console.log(newEvent);
    setEvents([...events, newEvent]);
    localStorage.setItem(STORAGE_KEY, JSON.stringify([...events, newEvent]));
  };

  useEffect(() => {
    const storedEvents = localStorage.getItem(STORAGE_KEY);
    if (storedEvents) {
      setEvents(JSON.parse(storedEvents));
    }
  }, []);

  return { events, handleClick };
};
