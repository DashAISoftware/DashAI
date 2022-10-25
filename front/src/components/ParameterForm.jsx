import React, { useState, useEffect, useRef } from 'react';
import PropTypes from 'prop-types';
import { useFormik } from 'formik';
import { P, StyledButton } from '../styles/globalComponents';
import { getDefaultValues } from '../utils/values';
import * as S from '../styles/components/ParameterFormStyles';

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
  const accordionRef = useRef(null);
  const handleButtonClick = () => {
    accordionRef.current.childNodes[0].childNodes[0].childNodes[0].click();
  };
  const getOptions = async (parentClass) => {
    const fetchedOptions = await fetch(
      `${process.env.REACT_APP_GET_CHILDREN_ENDPOINT + parentClass}`,
    );
    const receivedOptions = await fetchedOptions.json();
    setOptions(receivedOptions);
    setSelectedOption(receivedOptions[0]);
  };
  const getParamSchema = async () => {
    if (selectedOption !== '') {
      setDefaultValues({ ...defaultValues, loaded: false });
      const fetchedParams = await fetch(
        `${process.env.REACT_APP_SELECT_MODEL_ENDPOINT + selectedOption}`,
      );
      const parameterSchema = await fetchedParams.json();
      setParamSchema(parameterSchema);
      setDefaultValues({ loaded: true, values: getDefaultValues(parameterSchema) });
    }
  };
  useEffect(() => { getOptions(paramJsonSchema.parent); }, []);
  useEffect(() => { getParamSchema(); }, [selectedOption]);
  return (
    <div key={modelName}>
      <div>
        <S.FloatingLabel className="mb-3" label={modelName} style={{ display: 'inline-block', width: '90%' }}>
          <S.Select
            value={selectedOption}
            name="choice"
            onChange={(e) => setSelectedOption(e.target.value)}
          >
            {options.map((option) => <option key={option}>{option}</option>)}
          </S.Select>
        </S.FloatingLabel>
        <StyledButton
          type="button"
          style={{
            display: 'inline-block',
            marginLeft: '0.5rem',
            marginBottom: '1.5rem',
            fontSize: '0.8rem',
          }}
          onClick={handleButtonClick}
        >
          ⚙
        </StyledButton>
      </div>
      <S.Accordion ref={accordionRef} style={{ marginTop: '-0.5rem', marginBottom: '1rem', width: '90%' }}>
        <S.Accordion.Item eventKey="0">
          <S.Accordion.Header style={{ display: 'none' }}>{`${selectedOption} parameters`}</S.Accordion.Header>
          <S.Accordion.Body key={selectedOption}>
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
          </S.Accordion.Body>
        </S.Accordion.Item>
      </S.Accordion>
    </div>
  );
}

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
          <S.FloatingLabel className="mb-3" label={modelName} style={{ width: '90%' }}>
            <S.Input
              type="number"
              name={modelName}
              value={formik.values[modelName]}
              placeholder={1}
              onChange={formik.handleChange}
            />
          </S.FloatingLabel>
        </div>
      );

    case 'string':
      return (
        <div key={modelName}>
          <S.FloatingLabel className="mb-3" label={modelName} style={{ width: '90%' }}>
            <S.Select
              name={modelName}
              value={formik.values[modelName]}
              onChange={formik.handleChange}
              aria-label="select an option"
            >
              {
                paramJsonSchema
                  .enum
                  .map((option) => <option key={option} value={option}>{option}</option>)
              }
            </S.Select>
          </S.FloatingLabel>
        </div>
      );

    case 'number':
      return (
        <div key={modelName}>
          <S.FloatingLabel className="mb-3" label={modelName} style={{ width: '90%' }}>
            <S.Input
              type="number"
              name={modelName}
              value={formik.values[modelName]}
              placeholder={1}
              onChange={formik.handleChange}
            />
          </S.FloatingLabel>
        </div>
      );

    case 'boolean':
      return (
        <div key={modelName}>
          <S.FloatingLabel className="mb-3" label={modelName} style={{ width: '90%' }}>
            <S.Select
              name={modelName}
              value={formik.values[modelName]}
              onChange={formik.handleChange}
              aria-label="select an option"
            >
              <option key={`${modelName}-true`} value="True">True</option>
              <option key={`${modelName}-false`} value="False">False</option>
            </S.Select>
          </S.FloatingLabel>
        </div>
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
  modalShow,
  handleClose,
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
    modalShow: PropTypes.bool.isRequired,
    handleClose: PropTypes.func.isRequired,
  };
  if (Object.keys(parameterSchema).length === 0) {
    return (<div />);
  }
  // if (defaultValues === 'null') {
  //   return (<div />);
  // }
  const formik = useFormik({
    initialValues: getDefaultValues(parameterSchema),
    onSubmit: (values) => {
      setConfigByTableIndex(index, type, values);
      handleClose();
    },
  });
  return (
    <S.Modal show={modalShow} onHide={handleClose}>
      <S.Modal.Header>
        <P>Model parameters</P>
      </S.Modal.Header>
      <S.Modal.Body style={{ padding: '0px 10px' }}>
        <br />
        { genInput(type, parameterSchema, formik) }
      </S.Modal.Body>
      <S.Modal.Footer>
        <StyledButton onClick={formik.handleSubmit} style={{ float: 'right', width: '4rem' }}>Save</StyledButton>
        <StyledButton onClick={handleClose} style={{ float: 'right', width: '4rem' }}>Close</StyledButton>
      </S.Modal.Footer>
    </S.Modal>
  );
}

export default ParameterForm;
