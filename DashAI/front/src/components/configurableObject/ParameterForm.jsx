import React, { useState } from "react";
import PropTypes from "prop-types";
import { JsonForms } from "@jsonforms/react";
import { materialRenderers } from "@jsonforms/material-renderers";
import CustomObjectControlTester from "./CustomObjectControlTester";
import CustomObjectRenderer from "./CustomObjectRenderer";

function parameterForm({ parameterSchema }) {
  const [data, setData] = useState({});

  const renderers = [
    ...materialRenderers,
    // register custom renderers
    { tester: CustomObjectControlTester, renderer: CustomObjectRenderer },
  ];

  return (
    <JsonForms
      schema={parameterSchema}
      data={data}
      renderers={renderers}
      onChange={({ errors, data }) => setData(data)}
    />
  );
}

parameterForm.propTypes = {
  parameterSchema: PropTypes.objectOf(
    PropTypes.oneOfType([PropTypes.string, PropTypes.bool, PropTypes.object]),
  ).isRequired,
  initialValues: PropTypes.objectOf(
    PropTypes.oneOfType([
      PropTypes.string,
      PropTypes.bool,
      PropTypes.number,
      PropTypes.object,
    ]),
  ),
};

export default parameterForm;
