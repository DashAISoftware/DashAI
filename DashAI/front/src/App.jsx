import React from "react";

import { BrowserRouter, Route, Routes } from "react-router-dom";
import { Container } from "@mui/material";

import "./App.css";
import Data from "./tabs/Data";
import ExperimentsPage from "./pages/ExperimentPage";
import Results from "./tabs/Results";
import Home from "./pages/Home";
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
          <Route path="/app/results" element={<Results />}>
            <Route path="experiments/:id" element={<Results />} />
          </Route>
        </Routes>
      </Container>
    </BrowserRouter>
  );
}
export default App;
