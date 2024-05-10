import React from "react";

import { BrowserRouter, Route, Routes } from "react-router-dom";

import "./App.css";
import DatasetsPage from "./pages/datasets/Datasets";
import ExperimentsPage from "./pages/experiments/Experiments";
import Home from "./pages/home/Home";
import ResponsiveAppBar from "./components/ResponsiveAppBar";

function App() {
  return (
    <BrowserRouter>
      <ResponsiveAppBar />
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/app" element={<Home />} />
        <Route path="/app/data/" element={<DatasetsPage />} />
        <Route path="/app/experiments" element={<ExperimentsPage />} />
      </Routes>
    </BrowserRouter>
  );
}
export default App;
