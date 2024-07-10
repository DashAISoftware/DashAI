import React from "react";

import { BrowserRouter, Route, Routes } from "react-router-dom";

import "./App.css";
import DatasetsPage from "./pages/DatasetsPage";
import Experiments from "./pages/experiments/Experiments";
import RunResults from "./components/results/RunResults";
import ResultsPage from "./pages/ResultsPage";
import Home from "./pages/Home";
import ResponsiveAppBar from "./components/ResponsiveAppBar";

function App() {
  return (
    <BrowserRouter>
      <ResponsiveAppBar />
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/app" element={<Home />} />
        <Route path="/app/data/" element={<DatasetsPage />} />
        <Route path="/app/experiments" element={<Experiments />} />
        <Route path="/app/results">
          <Route index element={<ResultsPage />} />
          <Route path="experiments/:id">
            <Route index element={<ResultsPage />} />
            <Route path="runs/:id" element={<RunResults />} />
          </Route>
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
export default App;
