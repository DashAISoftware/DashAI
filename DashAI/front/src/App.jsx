import React, { useEffect, useState } from 'react';
// import { Container } from 'react-bootstrap';
// import { React, useState, useEffect } from 'react';
// import logo from './logo.svg';
import './App.css';
// import { useRoutes } from 'react-router-dom';
import Main from './layouts/Main';
// import Results from './layouts/Results';
import Error from './components/Error';
import Navbar from './components/Navbar';
import { TabsProvider } from './context/TabsProvider';

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
    <TabsProvider>
      <Navbar />
      {apiIsOnline
        ? <Main />
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
    </TabsProvider>
  );
}
export default App;
