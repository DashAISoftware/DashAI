import React, { useState, useEffect } from 'react';
import { CustomContainer } from '../styles/globalComponents';
import Upload from '../components/Upload';

function Data() {
  // dataset state
  const EMPTY = 0;
  const [datasetState, setDatasetState] = useState(JSON.parse(localStorage.getItem('datasetState')) || EMPTY);
  useEffect(() => localStorage.setItem('datasetState', JSON.stringify(datasetState)), [datasetState]);
  //
  const [taskName, setTaskName] = useState(JSON.parse(localStorage.getItem('taskName')) || '');
  useEffect(() => localStorage.setItem('taskName', JSON.stringify(taskName)), [taskName]);
  return (
    <CustomContainer>
      <Upload
        datasetState={datasetState}
        setDatasetState={setDatasetState}
        taskName={taskName}
        setTaskName={setTaskName}
      />
    </CustomContainer>
  );
}

export default Data;
