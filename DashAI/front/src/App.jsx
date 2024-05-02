import React from "react";

import { BrowserRouter, Route, Routes } from "react-router-dom";

import "./App.css";
import DatasetsPage from "./pages/DatasetsPage";
import ExperimentsPage from "./pages/ExperimentPage";
import ExplainersDashboard from "./components/explainers/ExplainersDashboard";
import ExplainersPage from "./pages/ExplainersPage";
import RunResults from "./components/results/RunResults";
import ResultsPage from "./pages/ResultsPage";
import Test from "./pages/test";
import Home from "./pages/Home";
import ResponsiveAppBar from "./components/ResponsiveAppBar";
import ExplainerData from "./components/explainers/ExplainerData";

function App() {
  return (
    <BrowserRouter>
      <ResponsiveAppBar />
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
        <Route path="/app/explainers">
          <Route index element={<ExplainersPage />} />
          <Route path="runs/:id" element={<ExplainersDashboard />} />
          <Route
            path="explainer/:scope/:runId/:id"
            element={<ExplainerData />}
          />
        </Route>
        <Route path="/app/test" element={<Test />} />
      </Routes>
    </BrowserRouter>
  );
}
export default App;
