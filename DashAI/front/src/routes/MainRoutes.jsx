import React from 'react';
// import { Routes, Route } from 'react-router-dom';
import { useRoutes } from 'react-router-dom';
import Home from '../components/Home';
import Upload from '../components/Upload';

const routes = [
  { path: '/', element: <Home /> },
  { path: '/data', element: <Upload /> },
];

function MainRoutes() {
  const routeResult = useRoutes(routes);
  return routeResult;
}

export default MainRoutes;
