// import React, { useState } from 'react';
import React from 'react';
import { Container } from 'react-bootstrap';
import ExperimentsTable from '../components/ExperimentsTable';
import ListObjects from '../components/List';

function Home() {
  const toDate = (timestamp) => {
    const dateConverter = new Intl.DateTimeFormat(
      'en-US',
      {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
      },
    );
    return dateConverter.format(timestamp);
  };
  const rows = [
    {
      name: 'myProject',
      created: toDate(Date.now()),
      edited: toDate(Date.now()),
      taskName: 'NumericClassification',
      dataset: 'Iris',
    },
    {
      name: 'myProject2',
      created: toDate(Date.now()),
      edited: toDate(Date.now()),
      taskName: 'TextClassification',
      dataset: 'twitterDataset',
    },

  ];
  // const [experimentsInTable, setExperimentsInTable] = useState(rows);
  // const removeExperimentFactory = (index) => {
  //   console.log(index);
  //   const experimentsArray = [...experimentsInTable];
  //   experimentsArray.splice(index, 1);
  //   setExperimentsInTable(experimentsArray);
  // };
  return (
    <Container>
      <button type="button" style={{ marginTop: '50px' }}>+ New Experiment</button>
      <ExperimentsTable
        rows={rows}
        removeExperimentFactory={() => {}}
      />
      <ListObjects saludo="hola mundo" />
    </Container>
  );
}

export default Home;
