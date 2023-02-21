import React from 'react';
// import { Routes, Route } from 'react-router-dom';
import { useRoutes } from 'react-router-dom';
// import Upload from '../components/Upload';
// import { Data, Experiment, Results, Play } from '../tabs';
import Home from '../tabs/Home';
import Data from '../tabs/Data';
import Experiment from '../tabs/Experiment';
import Results from '../tabs/Results';
import Play from '../tabs/Play';

const routes = [
  { path: '/', element: <Home /> },
  { path: '/data', element: <Data /> },
  { path: '/experiment', element: <Experiment /> },
  { path: '/results', element: <Results /> },
  { path: '/play', element: <Play /> },
];

function MainRoutes() {
  const routeResult = useRoutes(routes);
  return routeResult;
}

export default MainRoutes;
