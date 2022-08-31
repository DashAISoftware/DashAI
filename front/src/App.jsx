import React from 'react';
// import { React, useState, useEffect } from 'react';
// import logo from './logo.svg';
import './App.css';
import ExperimentConfiguration from './layouts/ExperimentConfiguration2';
// import ExperimentConfiguration from './layouts/ExperimentConfiguration';

// function App() {
//   return (
//     <div className="App">
//       <header className="App-header">
//         <img src={logo} className="App-logo" alt="logo" />
//         <p>
//           Edit
//           <code> src/App.js </code>
//           and save to reload.
//         </p>
//         <a
//           className="App-link"
//           href="https://reactjs.org"
//           target="_blank"
//           rel="noopener noreferrer"
//         >
//           Learn React
//         </a>
//       </header>
//     </div>
//   );
// }

// function getData(f) {
//   fetch(
//     'numericalWrapperForText.json',
//     {
//       headers: {
//         'Content-Type': 'application/json',
//       },
//     },
//   )
//     .then(
//       (response) => response.json(),
//     )
//     .then(
//       (d) => {
//         f(d);
//       },
//     );
// }

function App() {
  // const [data, setData] = useState({});
  // console.log(data.additionalProperties);
  // useEffect(() => {
  //   getData(setData);
  // }, []);
  //
  return (
    <ExperimentConfiguration />
  );
}
export default App;
