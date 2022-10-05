import React, { useState, useEffect } from 'react';
import {
  Card,
  Button,
  Accordion,
} from 'react-bootstrap';
import styled from 'styled-components';
import PropTypes from 'prop-types';
import { useFormik } from 'formik';

const Label = styled.label`
  font-weight: 600;
  margin-right: 10px;
`;

const Div = styled.div`
  margin-top: 10px;
`;

function getDefaultValues(parameterJsonSchema) {
  const { properties } = parameterJsonSchema;
  if (typeof properties !== 'undefined') {
    const parameters = Object.keys(properties);
    const defaultValues = {};
    parameters.forEach((param) => {
      const val = properties[param].oneOf[0].default;
      defaultValues[param] = typeof val !== 'undefined' ? val : { choice: '' };
    });
    // const defaultValues = parameters.reduce(
    //   (prev, current) => ({
    //     ...prev,
    //     [current]: properties[current].oneOf[0].default || {},
    //   }),
    //   {},
    // );
    return (defaultValues);
  }
  return ('null');
}

function ClassInput({ modelName, paramJsonSchema, setFieldValue }) {
  ClassInput.propTypes = {
    modelName: PropTypes.string.isRequired,
    paramJsonSchema: PropTypes.objectOf(
      PropTypes.oneOfType([
        PropTypes.string,
        PropTypes.bool,
        PropTypes.object,
      ]),
    ).isRequired,
    setFieldValue: PropTypes.func.isRequired,
  };
  const [options, setOptions] = useState([]);
  const [selectedOption, setSelectedOption] = useState('');
  const [paramSchema, setParamSchema] = useState({});
  const [defaultValues, setDefaultValues] = useState({ loaded: false, values: {} });
  const getOptions = async (parentClass) => {
    const fetchedOptions = await fetch(
      `http://localhost:8000/getChildren/${parentClass}`,
    );
    const receivedOptions = await fetchedOptions.json();
    setOptions(receivedOptions);
    setSelectedOption(receivedOptions[0]);
  };
  const getParamSchema = async () => {
    if (selectedOption !== '') {
      setDefaultValues({ ...defaultValues, loaded: false });
      const fetchedParams = await fetch(`http://localhost:8000/selectModel/${selectedOption}`);
      const parameterSchema = await fetchedParams.json();
      setParamSchema(parameterSchema);
      setDefaultValues({ loaded: true, values: getDefaultValues(parameterSchema) });
    }
  };
  useEffect(() => { getOptions(paramJsonSchema.parent); }, []);
  useEffect(() => { getParamSchema(); }, [selectedOption]);
  return (
    <Div key={modelName}>
      <div>
        <Label htmlFor={modelName}>{modelName}</Label>
        <select value={selectedOption} name="choice" onChange={(e) => setSelectedOption(e.target.value)}>
          {options.map((option) => <option key={option}>{option}</option>)}
        </select>
      </div>
      <Accordion style={{ marginTop: '10px' }}>
        <Accordion.Item eventKey="0">
          <Accordion.Header>{`${selectedOption} parameters`}</Accordion.Header>
          <Accordion.Body key={selectedOption}>
            {
            defaultValues.loaded
            && (
            <SubForm
              name={modelName}
              parameterSchema={paramSchema}
              setFieldValue={setFieldValue}
              choice={selectedOption}
              defaultValues={defaultValues.values}
            />
            )
          }
          </Accordion.Body>
        </Accordion.Item>
      </Accordion>
    </Div>
  );
}

const genInput = (modelName, paramJsonSchema, formik) => {
  const { type, properties } = paramJsonSchema;
  switch (type) {
    case 'object':
      return (
        <Div key={modelName}>
          {
            Object.keys(properties)
              .map((parameter) => genInput(
                parameter,
                properties[parameter].oneOf[0],
                formik,
              ))
          }
        </Div>
      );

    case 'integer':
      return (
        <Div key={modelName}>
          <Label htmlFor={modelName}>{modelName}</Label>
          <input
            type="number"
            name={modelName}
            id={modelName}
            value={formik.values[modelName]}
            onChange={formik.handleChange}
          />
        </Div>
      );

    case 'string':
      return (
        <Div key={modelName}>
          <Label htmlFor={modelName}>{modelName}</Label>
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
        </Div>
      );

    case 'number':
      return (
        <Div key={modelName}>
          <Label htmlFor={modelName}>{modelName}</Label>
          <input
            type="number"
            name={modelName}
            id={modelName}
            value={formik.values[modelName]}
            onChange={formik.handleChange}
          />
        </Div>
      );

    case 'boolean':
      return (
        <Div key={modelName}>
          <Label htmlFor={modelName}>{modelName}</Label>
          <select
            name={modelName}
            id={modelName}
            value={formik.values[modelName]}
            onChange={formik.handleChange}
          >
            <option key={`${modelName}-true`} value="True">True</option>
            <option key={`${modelName}-false`} value="False">False</option>
          </select>
        </Div>
      );

    case 'class':
      return (
        <ClassInput
          modelName={modelName}
          paramJsonSchema={paramJsonSchema}
          setFieldValue={formik.setFieldValue}
          key={`rec-param-${modelName}`}
        />
      );

    default:
      return (
        <p style={{ color: 'red', fontWeight: 'bold' }}>{`Not a valid parameter type: ${type}`}</p>
      );
  }
};

function SubForm({
  name,
  parameterSchema,
  setFieldValue,
  choice,
  defaultValues,
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
    choice: PropTypes.string.isRequired,
    defaultValues: PropTypes.objectOf(
      PropTypes.oneOfType([
        PropTypes.string,
        PropTypes.number,
        PropTypes.bool,
        PropTypes.object,
      ]),
    ).isRequired,
  };

  SubForm.defaultProps = {
    name: 'undefined',
  };
  // const defaultValues = getDefaultValues(parameterSchema);
  const newDefaultValues = { ...defaultValues, choice };
  const formik = useFormik({
    initialValues: newDefaultValues,
  });
  useEffect(() => {
    setFieldValue(name, formik.values);
  }, [formik.values]);

  return (
    <div key={`parameterForm-${choice}`}>
      { genInput(name, parameterSchema, formik) }
    </div>
  );
}

function ParameterForm({
  type,
  index,
  parameterSchema,
  setConfigByTableIndex,
  // defaultValues,
}) {
  ParameterForm.propTypes = {
    type: PropTypes.string.isRequired,
    index: PropTypes.number.isRequired,
    parameterSchema: PropTypes.objectOf(
      PropTypes.oneOfType([
        PropTypes.string,
        PropTypes.bool,
        PropTypes.object,
      ]),
    ).isRequired,
    setConfigByTableIndex: PropTypes.func.isRequired,
  };
  if (Object.keys(parameterSchema).length === 0) {
    return (<div />);
  }
  // if (defaultValues === 'null') {
  //   return (<div />);
  // }
  const formik = useFormik({
    initialValues: getDefaultValues(parameterSchema),
    onSubmit: (values) => setConfigByTableIndex(index, type, values),
  });
  return (
    <Card className="sm-6">
      <Card.Header>Model parameters</Card.Header>
      <div style={{ padding: '40px 10px' }}>
        { genInput(type, parameterSchema, formik) }
      </div>
      <Card.Footer>
        <Button variant="dark" onClick={formik.handleSubmit} style={{ width: '100%' }}>Save</Button>
      </Card.Footer>
    </Card>
  );
}

export default ParameterForm;
