import React from "react";
import "./App.css";
import ResponsiveAppBar from "./components/ResponsiveAppBar";

import Home from "./tabs/Home";
import Data from "./tabs/Data";
import Experiment from "./tabs/Experiment";
import Results from "./tabs/Results";
import Play from "./tabs/Play";
import { BrowserRouter, Route, Routes } from "react-router-dom";
import Container from "@mui/material/Container";
import { Grid } from "@mui/material";

function App() {
  return (
    <React.Fragment>
      <BrowserRouter>
        <ResponsiveAppBar />
        <Container maxWidth="lg" sx={{ my: 5, mb: 4 }}>
          <Grid
            container
            direction="row"
            justifyContent="center"
            alignItems="center"
          >
            <Routes>
              <Route path="/" element={<Home />}></Route>
              <Route path="/app" element={<Home />} />
              <Route path="/app/data/" element={<Data />} />
              <Route path="/app/experiments" element={<Experiment />} />
              <Route path="/app/results" element={<Results />} />
              <Route path="/app/play" element={<Play />} />
            </Routes>
          </Grid>
        </Container>
      </BrowserRouter>
    </React.Fragment>
  );
}
export default App;
