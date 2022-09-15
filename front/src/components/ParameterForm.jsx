import React, { useEffect } from 'react';
import {
  Card,
  Button,
  Accordion,
} from 'react-bootstrap';
import PropTypes from 'prop-types';
import uuid from 'react-uuid';
import { useFormik } from 'formik';

const genInput = (modelName, paramJsonSchema, formik) => {
  const { type, properties } = paramJsonSchema;
  switch (type) {
    case 'object':
      return (
        <div key={modelName}>
          {
            Object.keys(properties)
              .map((parameter) => genInput(
                parameter,
                properties[parameter].oneOf[0],
                formik,
              ))
          }
        </div>
      );

    case 'integer':
      return (
        <div key={modelName}>
          <label htmlFor={modelName}>{modelName}</label>
          <input
            type="number"
            name={modelName}
            id={modelName}
            value={formik.values[modelName]}
            onChange={formik.handleChange}
          />
        </div>
      );

    case 'string':
      return (
        <div key={modelName}>
          <label htmlFor={modelName}>{modelName}</label>
          <select
            name={modelName}
            id={modelName}
            value={formik.values[modelName]}
            onChange={formik.handleChange}
          >
            {
              paramJsonSchema
                .enum
                .map((option) => <option key={option} value={option}>{option}</option>)
            }
          </select>
        </div>
      );

    case 'number':
      return (
        <div key={modelName}>
          <label htmlFor={modelName}>{modelName}</label>
          <input
            type="number"
            name={modelName}
            id={modelName}
            value={formik.values[modelName]}
            onChange={formik.handleChange}
          />
        </div>
      );

    case 'boolean':
      return (
        <div key={modelName}>
          <label htmlFor={modelName}>{modelName}</label>
          <select
            name={modelName}
            id={modelName}
            value={formik.values[modelName]}
            onChange={formik.handleChange}
          >
            <option key={`${modelName}-true`} value="True">True</option>
            <option key={`${modelName}-false`} value="False">False</option>
          </select>
        </div>
      );

    case 'class':
      return (
        <div key={modelName}>
          <div>
            <label htmlFor={modelName}>{modelName}</label>
            <select>
              <option>{paramJsonSchema.parent}</option>
            </select>
          </div>
          <Accordion>
            <Accordion.Item eventKey="0">
              <Accordion.Header>{`${modelName} parameters`}</Accordion.Header>
              <Accordion.Body>
                <SubForm
                  name={modelName}
                  parameterSchema={{}}
                  setFieldValue={formik.setFieldValue}
                />
              </Accordion.Body>
            </Accordion.Item>
          </Accordion>
        </div>
      );

    default:
      return (
        <p style={{ color: 'red', fontWeight: 'bold' }}>{`Not a valid parameter type: ${type}`}</p>
      );
  }
};

function getDefaultValues(parameterJsonSchema) {
  const { properties } = parameterJsonSchema;
  if (typeof properties !== 'undefined') {
    const parameters = Object.keys(properties);
    const defaultValues = parameters.reduce(
      (prev, current) => ({
        ...prev,
        [current]:
             properties[current].oneOf[0].default
          || properties[current].oneOf[0].deafult
          || {},
      }),
      {},
    );
    return (defaultValues);
  }
  return ('null');
}

function SubForm({
  name,
  parameterSchema,
  setFieldValue,
}) {
  SubForm.propTypes = {
    name: PropTypes.string,
    parameterSchema: PropTypes.objectOf(
      PropTypes.oneOfType([
        PropTypes.string,
        PropTypes.bool,
        PropTypes.object,
      ]),
    ).isRequired,
    setFieldValue: PropTypes.func.isRequired,
  };

  SubForm.defaultProps = {
    name: 'undefined',
  };
  const defaultValues = getDefaultValues(parameterSchema);
  if (defaultValues === 'null') {
    return (<p>Recursion</p>);
  }
  const formik = useFormik({
    initialValues: defaultValues,
  });
  useEffect(() => {
    setFieldValue(name, formik.values);
  }, [formik.values]);

  return (
    <div key={uuid()}>
      { genInput(name, parameterSchema, formik) }
    </div>
  );
}

function ParameterForm({
  name,
  parameterSchema,
}) {
  ParameterForm.propTypes = {
    name: PropTypes.string,
    parameterSchema: PropTypes.objectOf(
      PropTypes.oneOfType([
        PropTypes.string,
        PropTypes.bool,
        PropTypes.object,
      ]),
    ).isRequired,
  };

  ParameterForm.defaultProps = {
    name: 'undefined',
  };
  const defaultValues = getDefaultValues(parameterSchema);
  if (defaultValues === 'null') {
    return (<div />);
  }
  const formik = useFormik({
    initialValues: defaultValues,
    onSubmit: (values) => console.log(values),
  });
  return (
    <Card className="sm-6">
      <Card.Header>Model parameters</Card.Header>
      <div style={{ padding: '40px 10px' }}>
        { genInput(name, parameterSchema, formik) }
      </div>
      <Card.Footer>
        <Button variant="dark" onClick={formik.handleSubmit} style={{ width: '100%' }}>Save</Button>
      </Card.Footer>
    </Card>
  );
}

export default ParameterForm;
