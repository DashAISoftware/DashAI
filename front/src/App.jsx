import React, { useEffect, useState } from 'react';
// import { Container } from 'react-bootstrap';
// import { React, useState, useEffect } from 'react';
// import logo from './logo.svg';
import './App.css';
import { useRoutes } from 'react-router-dom';
import ExperimentPipeline from './layouts/ExperimentPipeline';
// import Results from './layouts/Results';
import Error from './components/Error';
import Navbar from './components/Navbar';

function App() {
  const [apiIsOnline, setApiIsOnline] = useState(true);
  useEffect(
    () => {
      async function apiOnlineTest() {
        try {
          const fetchApiState = await fetch(`${process.env.REACT_APP_STATE_ENDPOINT}`);
          const apiState = await fetchApiState.json();
          setApiIsOnline(apiState.state === 'online');
        } catch (e) {
          setApiIsOnline(false);
        }
      }
      apiOnlineTest();
    },
    [],
  );
  const element = useRoutes([
    { path: '/', element: <ExperimentPipeline /> },
    // { path: 'results/:sessionId', element: <Results /> },
    // { path: 'error', element: <Error /> },
  ]);
  return (
    <div>
      <Navbar />
      {apiIsOnline
        ? element
        : (
          <div style={{
            marginLeft: '30.3vw',
            marginTop: '30vh',
            textAlign: 'center',
          }}
          >
            <Error message="API is not online" />
          </div>
        )}
    </div>
  );
}
export default App;
