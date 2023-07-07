import React from "react";

import { BrowserRouter, Route, Routes } from "react-router-dom";
import { Container } from "@mui/material";

import "./App.css";
import DatasetsPage from "./pages/DatasetsPage";
import ExperimentsPage from "./pages/ExperimentPage";
import RunResults from "./components/results/RunResults";
import ResultsPage from "./pages/ResultsPage";
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
          <Route path="/app/data/" element={<DatasetsPage />} />
          <Route path="/app/experiments" element={<ExperimentsPage />} />
          <Route path="/app/results">
            <Route index element={<ResultsPage />} />
            <Route path="experiments/:id">
              <Route index element={<ResultsPage />} />
              <Route path="runs/:id" element={<RunResults />} />
            </Route>
          </Route>
        </Routes>
      </Container>
    </BrowserRouter>
  );
}
export default App;
