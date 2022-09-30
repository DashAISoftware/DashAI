import React from 'react';
// import { React, useState, useEffect } from 'react';
// import logo from './logo.svg';
import './App.css';
import { useRoutes } from 'react-router-dom';
import ExperimentConfiguration from './layouts/ExperimentConfiguration';
import Results from './layouts/Results';

function App() {
  const element = useRoutes([
    { path: '/', element: <ExperimentConfiguration /> },
    { path: 'results/:sessionId', element: <Results /> },
  ]);
  return (element);
}
export default App;
