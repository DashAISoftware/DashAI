import React from 'react';
import PropTypes from 'prop-types';

function List({ saludo }) {
  const fetched = async (model) => {
    const data = await fetch(`${process.env.REACT_APP_SELECT_SCHEMA_ENDPOINT + model}`);
    console.log(data);
  };
  fetched('task/tasks');
  return (
    <div>
      <h1>{saludo}</h1>
    </div>
  );
}
List.propTypes = {
  saludo: PropTypes.string.isRequired,
};
export default List;
