import React from 'react';
// import { React, useState, useEffect } from 'react';
// import logo from './logo.svg';
import './App.css';
import { useRoutes } from 'react-router-dom';
import ExperimentPipeline from './layouts/ExperimentPipeline';
// import Results from './layouts/Results';
import Error from './layouts/Error';
import Navbar from './components/Navbar';

function App() {
  const element = useRoutes([
    { path: '/', element: <ExperimentPipeline /> },
    // { path: 'results/:sessionId', element: <Results /> },
    { path: 'error', element: <Error /> },
  ]);
  return (
    <div>
      <Navbar />
      { element }
    </div>
  );
}
export default App;
