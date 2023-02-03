import React, { useState, useEffect } from 'react';
import PropTypes from 'prop-types';

function List({ route }) {
  const [listItems, setList] = useState([]);

  useEffect(() => {
    async function fetchList() {
      const response = await fetch(`${process.env.REACT_APP_SELECT_SCHEMA_ENDPOINT + route}`);
      const model = await response.json();
      setList(model.tasks);
    }
    fetchList();
  }, []);
  return (
    <div style={{ color: 'white' }}>
      <h1>Taks</h1>
      <ul>{(listItems.map((item) => <li key={item.name}>{item.class}</li>))}</ul>
    </div>
  );
}

List.propTypes = {
  route: PropTypes.string.isRequired,
};
export default List;
