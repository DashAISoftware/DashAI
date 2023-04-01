import React from "react";
// import { Routes, Route } from 'react-router-dom';
import { useRoutes } from "react-router-dom";
// import Upload from '../components/Upload';
// import { Data, Experiment, Results, Play } from '../tabs';
import Home from "../tabs/Home";
import Data from "../tabs/Data";
import Experiment from "../tabs/Experiment";
import Results from "../tabs/Results";
import Play from "../tabs/Play";

const routes = [
  { path: "/app", element: <Home /> },
  { path: "/app/data", element: <Data /> },
  { path: "/app/experiment", element: <Experiment /> },
  { path: "/app/results", element: <Results /> },
  { path: "/app/play", element: <Play /> },
];

function MainRoutes() {
  const routeResult = useRoutes(routes);
  return routeResult;
}

export default MainRoutes;
