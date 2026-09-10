import React, { createContext, useState, useMemo, useEffect } from "react";
import { ThemeProvider, createTheme } from "@mui/material/styles";
import getTheme from "../styles/theme";
import { useTranslation } from "react-i18next";

export const ColorModeContext = createContext({ toggleColorMode: () => {} });

export function CustomThemeProvider({ children }) {
  const [mode, setMode] = useState(() => {
    // Load saved theme from localStorage or default to dark
    const savedMode = localStorage.getItem("themeMode");
    return savedMode || "dark";
  });
  const { i18n } = useTranslation();

  // Save theme preference to localStorage whenever it changes
  useEffect(() => {
    localStorage.setItem("themeMode", mode);
  }, [mode]);

  const colorMode = useMemo(
    () => ({
      toggleColorMode: () => {
        setMode((prevMode) => (prevMode === "light" ? "dark" : "light"));
      },
    }),
    [],
  );

  const theme = useMemo(() => createTheme(getTheme(mode)), [mode]);

  // Plotly.js hardcodes its updatemenus (dropdown selector) hover/active item
  // background to a near-white color with no layout option to override it -
  // see plotly.js/src/components/updatemenus/constants.js. Stamping the mode
  // here lets a plain CSS rule (index.css) neutralize it in dark mode only,
  // where it makes the selected item's text unreadable.
  useEffect(() => {
    document.documentElement.dataset.theme = mode;
    document.documentElement.style.setProperty(
      "--dashai-plot-menu-highlight",
      theme.palette.background.paper,
    );
  }, [mode, theme]);

  return (
    <ColorModeContext.Provider value={colorMode}>
      <ThemeProvider theme={theme}>{children}</ThemeProvider>
    </ColorModeContext.Provider>
  );
}
