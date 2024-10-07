import React, { useState } from 'react';
import PropTypes from 'prop-types';
import { GridActionsCellItem } from '@mui/x-data-grid';
import { AccountTree } from '@mui/icons-material';
import {
  Dialog,
  DialogContent,
  DialogTitle,
  DialogActions,
  Button,
} from '@mui/material';
import ReactFlow from "reactflow";
import "reactflow/dist/style.css";
import experimentToNodes from "./ExperimentToNodes";

function PipelinesModal({ experiment }) {
  const [open, setOpen] = useState(false);

  const handleOpenModal = () => {
    console.log('Experiment data:', experiment); 
    setOpen(true);
  };

  const handleCloseContent = () => {
    setOpen(false);
  };

  const { nodes, edges } = experimentToNodes(experiment);

  /*
  const initialNodes = [
    { id: '1', position: { x: 0, y: 0 }, data: { label: '1' } },
    { id: '2', position: { x: 0, y: 100 }, data: { label: '2' } },
  ];
  const initialEdges = [{ id: 'e1-2', source: '1', target: '2' }];
  */

  return (
    <React.Fragment>
      <GridActionsCellItem
        key="pipelines-modal"
        icon={<AccountTree />}
        label="Pipelines"
        onClick={handleOpenModal}
        sx={{ color: "success.main" }}
      />
      <Dialog
        open={open}
        onClose={handleCloseContent}
        fullWidth
        maxWidth={"md"}
      >
        <DialogTitle>Pipelines</DialogTitle>
        <DialogContent>
          <div style={{ width: '40vw', height: '40vh' }}>
            <ReactFlow nodes={nodes} edges={edges} />
          </div>
        </DialogContent>
        <DialogActions>
          <Button
            onClick={handleCloseContent}
            autoFocus
            variant="contained"
            color="primary"
          >
            Close
          </Button>
        </DialogActions>
      </Dialog>
    </React.Fragment>
  );
}

PipelinesModal.propTypes = {
  experiment: PropTypes.object.isRequired,
};

export default PipelinesModal;
