import React from "react";
import ReactDOM from "react-dom/client";
import "./index.css";
import { BrowserRouter as Router } from "react-router-dom";
import { createTheme, ThemeProvider } from "@mui/material/styles";
import CssBaseline from "@mui/material/CssBaseline";
import App from "./App";
import reportWebVitals from "./reportWebVitals";
import "bootstrap/dist/css/bootstrap.min.css";
import theme from "./styles/theme";
import GlobalStyle from "./styles/globalStyles";
import muiGlobalStyle from "./styles/muiGlobalStyles";

const root = ReactDOM.createRoot(document.getElementById("root"));
const myTheme = createTheme({ ...theme, ...muiGlobalStyle });
root.render(
  <React.StrictMode>
    <Router>
      <GlobalStyle />
      <ThemeProvider theme={myTheme}>
        <CssBaseline />
        <App />
      </ThemeProvider>
    </Router>
  </React.StrictMode>
);

// If you want to start measuring performance in your app, pass a function
// to log results (for example: reportWebVitals(console.log))
// or send to an analytics endpoint. Learn more: https://bit.ly/CRA-vitals
reportWebVitals();
