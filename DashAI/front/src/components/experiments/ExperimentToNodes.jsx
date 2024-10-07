export default function experimentToNodes(experiment) {
    const nodes = [
      {
        id: 'dataset', 
        position: { x: 0, y: 0 }, 
        data: { label: `Dataset: ${experiment.dataset_id}` },
        style: { minWidth: 100, padding: 10 },   
        sourcePosition: 'right',
      },
      {
        id: 'task', 
        position: { x: 200, y: 0 },  
        data: { label: `Task: ${experiment.task_name}` },
        style: { minWidth: 100, padding: 10 },   
        targetPosition: 'left',
        sourcePosition: 'right',
      },
      {
        id: 'input_columns', 
        position: { x: 400, y: 0 },  
        data: { label: `Input Columns: ${experiment.input_columns.join(', ')}` },
        style: { minWidth: 100, padding: 10 },   
        targetPosition: 'left',
        sourcePosition: 'right',
      },
      {
        id: 'output_columns', 
        position: { x: 600, y: 0 },  
        data: { label: `Output Columns: ${experiment.output_columns.join(', ')}` },
        style: { minWidth: 100, padding: 10 },   
        targetPosition: 'left',
        sourcePosition: 'right',
      },
      {
        id: 'splits', 
        position: { x: 800, y: 0 },  
        data: { label: `Splits: Train ${JSON.parse(experiment.splits).train}, Validation ${JSON.parse(experiment.splits).validation}, Test ${JSON.parse(experiment.splits).test}` },
        style: { minWidth: 100, padding: 10 },   
        targetPosition: 'left',
      }
    ];
  
    const edges = [
      { id: 'e1', source: 'dataset', target: 'task' },
      { id: 'e2', source: 'task', target: 'input_columns' },
      { id: 'e3', source: 'input_columns', target: 'output_columns' },
      { id: 'e4', source: 'output_columns', target: 'splits' }
    ];
  
    return { nodes, edges };
}
  