import React from "react";

import { BrowserRouter, Route, Routes } from "react-router-dom";

import "./App.css";
import DatasetsPage from "./pages/datasets/Datasets";
import ExperimentsPage from "./pages/experiments/Experiments";
import Home from "./pages/home/Home";
import ExplainersDashboard from "./components/explainers/ExplainersDashboard";
import ExplainersPage from "./pages/ExplainersPage";
import ExplainerData from "./components/explainers/ExplainerData";
import ResponsiveAppBar from "./components/ResponsiveAppBar";
import PluginsPage from "./pages/plugins/Plugins";
import PluginsDetails from "./pages/plugins/components/PluginsDetails";

function App() {
  return (
    <BrowserRouter>
      <ResponsiveAppBar />
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/app" element={<Home />} />
        <Route path="/app/data/" element={<DatasetsPage />} />
        <Route path="/app/experiments" element={<ExperimentsPage />} />
        <Route path="/app/explainers">
          <Route index element={<ExplainersPage />} />
          <Route path="runs/:id" element={<ExplainersDashboard />} />
          <Route
            path="explainer/:scope/:runId/:id"
            element={<ExplainerData />}
          />
        </Route>
        <Route path="/app/plugins">
          <Route index element={<PluginsPage />} />
          <Route path=":category">
            <Route index element={<PluginsPage />} />
            <Route path="details/:id" element={<PluginsDetails />} />
          </Route>
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
export default App;
