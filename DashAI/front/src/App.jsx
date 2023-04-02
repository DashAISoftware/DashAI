import React, { useEffect, useState } from "react";
import "./App.css";
import Error from "./components/Error";
import ResponsiveAppBar from "./components/ResponsiveAppBar";

import Home from "./tabs/Home";
import Data from "./tabs/Data";
import Experiment from "./tabs/Experiment";
import Results from "./tabs/Results";
import Play from "./tabs/Play";
import { BrowserRouter, Route, Routes } from "react-router-dom";

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
    <div>
      {apiIsOnline ? (
        <BrowserRouter>
          <ResponsiveAppBar />
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/data/" element={<Data />} />
            <Route path="/experiments" element={<Experiment />} />
            <Route path="/results" element={<Results />} />
            <Route path="/play" element={<Play />} />
          </Routes>
        </BrowserRouter>
      ) : (
        <div
          style={{
            marginLeft: "30.3vw",
            marginTop: "30vh",
            textAlign: "center",
          }}
        >
          <Error message="API is not online" />
        </div>
      )}
    </div>
  );
}
export default App;
