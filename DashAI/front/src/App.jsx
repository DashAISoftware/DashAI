import React from "react";
import { Container } from "@mui/material";
import { BrowserRouter, Route, Routes } from "react-router-dom";

import "./App.css";
import ResponsiveAppBar from "./components/ResponsiveAppBar";
import Home from "./pages/Home";
import Data from "./tabs/Data";
import Experiment from "./tabs/Experiment";

function App() {
  return (
    <BrowserRouter>
      <ResponsiveAppBar />
      <Container maxWidth="lg" sx={{ my: 5, mb: 4 }}>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/app" element={<Home />} />
          <Route path="/app/data/" element={<Data />} />
          <Route path="/app/experiments" element={<Experiment />} />
          <Route path="/app/results" element={<div>TODO...</div>} />
        </Routes>
      </Container>
    </BrowserRouter>
  );
}
export default App;
