import React from "react";

import { BrowserRouter, Route, Routes } from "react-router-dom";
import { Container } from "@mui/material";

import "./App.css";
import Data from "./tabs/Data";
import ExperimentsPage from "./pages/ExperimentPage";
import Home from "./pages/Home";
import Dummy from "./tabs/Dummy";

import ResponsiveAppBar from "./components/ResponsiveAppBar";

function App() {
  return (
    <BrowserRouter>
      <ResponsiveAppBar />
      <Container maxWidth="lg" sx={{ my: 5, mb: 4 }}>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/app" element={<Home />} />
          <Route path="/app/data/" element={<Data />} />
          <Route path="/app/experiments" element={<ExperimentsPage />} />
          <Route path="/app/results" element={<div>TODO...</div>} />
          <Route path="/app/dummy" element={<Dummy />} />
        </Routes>
      </Container>
    </BrowserRouter>
  );
}
export default App;
