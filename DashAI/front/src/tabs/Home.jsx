import React, { useState } from 'react';
import { Container } from 'react-bootstrap';
import { StyledButton } from '../styles/globalComponents';
import ExperimentsTable from '../components/ExperimentsTable';
import SchemaList from '../components/SchemaList';

function Home() {
  const [selectedTask, setSelectedTask] = useState();
  const [showTaskModal, setShowTaskModal] = useState(false);
  const handleTaskModalClose = () => setShowTaskModal(false);

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
      <StyledButton
        variant="dark"
        onClick={() => setShowTaskModal(!showTaskModal)}
        style={{ margin: '50px 0px 20px' }}
      >
        + New Experiment
      </StyledButton>
      <ExperimentsTable
        rows={rows}
        removeExperimentFactory={() => {}}
      />
      <SchemaList
        schemaType="task"
        schemaName="tasks"
        listName="task"
        description="What do you want to do today?"
        showModal={showTaskModal}
        handleModalClose={handleTaskModalClose}
        output={setSelectedTask}
      />
      <h1 style={{ color: '#fff' }}>{`Selected: ${selectedTask}`}</h1>
    </Container>
  );
}

export default Home;
