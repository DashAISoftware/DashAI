import React, { useEffect, useState } from 'react';
// import { Container } from 'react-bootstrap';
// import { React, useState, useEffect } from 'react';
// import logo from './logo.svg';
import './App.css';
// import { useRoutes } from 'react-router-dom';
// import Main from './layouts/Main';
import MainRoutes from './routes/MainRoutes';
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
  // const element = useRoutes([
  //   { path: '/', element: <Home /> },
  //   { path: '/tabs', element: <ExperimentPipeline /> },
  // ]);
  return (
    <div>
      <Navbar />
      {apiIsOnline
        ? <MainRoutes />
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
