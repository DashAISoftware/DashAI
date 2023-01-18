/* eslint react/prop-types: 0 */
import React, {
  createContext,
  useContext,
  useState,
  useMemo,
} from 'react';

const ActiveTabContext = createContext();

export function TabsProvider({ children }) {
  const [activeTab, setActiveTab] = useState('home');

  const value = useMemo(() => ({ activeTab, setActiveTab }), [activeTab, setActiveTab]);

  return (
    <ActiveTabContext.Provider value={value}>
      {children}
    </ActiveTabContext.Provider>
  );
}

export function useActiveTab() {
  return useContext(ActiveTabContext);
}
