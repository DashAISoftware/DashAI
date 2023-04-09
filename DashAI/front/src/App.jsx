import React, { useEffect, useState } from "react";
import { Grid, Container } from "@mui/material";
import { BrowserRouter, Route, Routes } from "react-router-dom";

import "./App.css";
import Error from "./components/Error";
import ResponsiveAppBar from "./components/ResponsiveAppBar";
import Home from "./tabs/Home";
import Data from "./tabs/Data";
import ExperimentsPage from "./pages/ExperimentsPage";
import Results from "./tabs/Results";
import Play from "./tabs/Play";

function App() {
  const [apiIsOnline, setApiIsOnline] = useState(true);

  useEffect(() => {
    async function apiOnlineTest() {
      try {
        const apiState = await fetch(`${process.env.API_URL}`);
        setApiIsOnline(apiState.ok);
      } catch (e) {
        setApiIsOnline(false);
      }
    }
    apiOnlineTest();
  }, []);

  return (
    <React.Fragment>
      {apiIsOnline ? (
        <BrowserRouter>
          <ResponsiveAppBar />
          <Container maxWidth="lg" sx={{ my: 5, mb: 4 }}>
            <Routes>
              <Route path="/" element={<Home />}></Route>
              <Route path="/app" element={<Home />} />
              <Route path="/app/data/" element={<Data />} />
              <Route path="/app/experiments" element={<ExperimentsPage />} />
              <Route path="/app/results" element={<Results />} />
              <Route path="/app/play" element={<Play />} />
            </Routes>
          </Container>
        </BrowserRouter>
      ) : (
        <Container maxWidth="lg">
          <Grid
            container
            direction="row"
            justifyContent="center"
            alignItems="center"
            sx={{ mt: 6 }}
          >
            <Grid item>
              <Error message="API is not online" />
            </Grid>
          </Grid>
        </Container>
      )}
    </React.Fragment>
  );
}
export default App;
