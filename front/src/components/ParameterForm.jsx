import React, { useState, useEffect, useRef } from 'react';
import PropTypes from 'prop-types';
import { useFormik } from 'formik';
import * as Yup from 'yup';
import { P, StyledButton, ErrorMessageDiv } from '../styles/globalComponents';
import { getDefaultValues } from '../utils/values';
import * as S from '../styles/components/ParameterFormStyles';

function genYupValidation(yupInitialObj, schema) {
  let finalObj = yupInitialObj;
  if (Object.prototype.hasOwnProperty.call(schema, 'minimum')) {
    finalObj = finalObj.min(
      schema.minimum,
      schema.error_msg,
    );
  }

  if (Object.prototype.hasOwnProperty.call(schema, 'excluseiveMinimum')) {
    // TODO
  }

  if (Object.prototype.hasOwnProperty.call(schema, 'enum')) {
    finalObj = finalObj.oneOf(schema.enum);
  }
  return (finalObj.required('Required'));
}

function getValidation(parameterJsonSchema) {
  const { properties } = parameterJsonSchema;
  const validationObject = {};
  if (typeof properties !== 'undefined') {
    const parameters = Object.keys(properties);
    parameters.forEach((param) => {
      const subSchema = properties[param].oneOf[0];
      let yupInitialObj = null;
      switch (subSchema.type) {
        case ('integer'):
          yupInitialObj = Yup.number().integer();
          break;

        case ('number'):
          yupInitialObj = Yup.number();
          break;

        case ('string'):
          yupInitialObj = Yup.string();
          break;

        case ('boolean'):
          yupInitialObj = Yup.boolean();
          break;

        default:
          yupInitialObj = 'none';
      }
      if (yupInitialObj !== 'none') {
        validationObject[param] = genYupValidation(yupInitialObj, subSchema);
      }
    });
  }
  return (Yup.object().shape(validationObject));
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
        <S.InputContainerDiv key={modelName}>
          <S.FloatingLabel className="mb-3" label={modelName} style={{ width: '90%' }} hasError={formik.errors[modelName]}>
            <S.Input
              type="number"
              name={modelName}
              value={formik.values[modelName]}
              placeholder={1}
              onChange={formik.handleChange}
              hasError={formik.errors[modelName]}
            />
          </S.FloatingLabel>
          {formik.errors[modelName]
            ? <ErrorMessageDiv>{formik.errors[modelName]}</ErrorMessageDiv>
            : null}
        </S.InputContainerDiv>
      );

    case 'string':
      return (
        <S.InputContainerDiv key={modelName}>
          <S.FloatingLabel className="mb-3" label={modelName} style={{ width: '90%' }}>
            <S.Select
              name={modelName}
              value={formik.values[modelName]}
              onChange={formik.handleChange}
              aria-label="select an option"
              hasError={formik.errors[modelName]}
            >
              {
                paramJsonSchema
                  .enum
                  .map((option) => <option key={option} value={option}>{option}</option>)
              }
            </S.Select>
          </S.FloatingLabel>
          {formik.errors[modelName]
            ? <ErrorMessageDiv>{formik.errors[modelName]}</ErrorMessageDiv>
            : null}
        </S.InputContainerDiv>
      );

    case 'number':
      return (
        <S.InputContainerDiv key={modelName}>
          <S.FloatingLabel className="mb-3" label={modelName} style={{ width: '90%' }}>
            <S.Input
              type="number"
              name={modelName}
              value={formik.values[modelName]}
              placeholder={1}
              onChange={formik.handleChange}
            />
          </S.FloatingLabel>
        </S.InputContainerDiv>
      );

    case 'boolean':
      return (
        <S.InputContainerDiv key={modelName}>
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
        </S.InputContainerDiv>
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
    validationSchema: getValidation(parameterSchema),
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
  showModal,
  handleModalClose,
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
    showModal: PropTypes.bool.isRequired,
    handleModalClose: PropTypes.func.isRequired,
  };
  if (Object.keys(parameterSchema).length === 0) {
    return (<div />);
  }

  // const myValidationSchema = Yup.object().shape({
  //   algoritm: Yup.string()
  //     .oneOf(['auto', 'ball_tree', 'kd_tree'])
  //     .required('Required'),
  //   n_neighbors: Yup.number()
  //     .integer()
  //     .min(1, 'El parámetro n_neighbors debe ser de tipo entero mayor o igual a 1.')
  //     .required('Required'),
  //   weights: Yup.string()
  //     .oneOf(['uniform', 'distanc'])
  //     .required('Required'),
  // });
  // if (defaultValues === 'null') {
  //   return (<div />);
  // }
  // console.log(myValidationSchema);
  const formik = useFormik({
    initialValues: getDefaultValues(parameterSchema),
    validationSchema: getValidation(parameterSchema),
    onSubmit: (values) => {
      setConfigByTableIndex(index, type, values);
      handleModalClose();
    },
  });
  return (
    <S.Modal show={showModal} onHide={handleModalClose}>
      <S.Modal.Header>
        <P>Model parameters</P>
      </S.Modal.Header>
      <S.Modal.Body style={{ padding: '0px 10px' }}>
        <br />
        { genInput(type, parameterSchema, formik) }
      </S.Modal.Body>
      <S.Modal.Footer>
        <StyledButton onClick={formik.handleSubmit} style={{ float: 'right', width: '4rem' }}>Save</StyledButton>
        <StyledButton onClick={handleModalClose} style={{ float: 'right', width: '4rem' }}>Close</StyledButton>
      </S.Modal.Footer>
    </S.Modal>
  );
}

export default ParameterForm;
