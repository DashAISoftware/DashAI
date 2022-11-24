/* eslint-disable react/jsx-props-no-spreading */
import React, { useState, useEffect, useRef } from 'react';
import PropTypes from 'prop-types';
import { useFormik } from 'formik';
import * as Yup from 'yup';
import OverlayTrigger from 'react-bootstrap/OverlayTrigger';
import Tooltip from 'react-bootstrap/Tooltip';
// import Select from 'react-select';
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
  if (Object.prototype.hasOwnProperty.call(schema, 'exclusiveMinimum')) {
    finalObj = finalObj.min(
      Math.min(schema.exclusiveMinimum, schema.default),
      schema.error_msg,
    );
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

function ClassInput({
  modelName,
  paramJsonSchema,
  setFieldValue,
  formDefaultValues,
}) {
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
    formDefaultValues: PropTypes.objectOf(
      PropTypes.oneOfType([
        PropTypes.string,
        PropTypes.bool,
        PropTypes.number,
        PropTypes.object,
      ]),
    ),
  };
  ClassInput.defaultProps = {
    formDefaultValues: { emptyDefaultValues: true },
  };
  const [options, setOptions] = useState([]);
  const [selectedOption, setSelectedOption] = useState(formDefaultValues.choice);
  const [paramSchema, setParamSchema] = useState({});
  const [defaultValues, setDefaultValues] = useState({ loaded: true, values: formDefaultValues });
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
    // setSelectedOption(receivedOptions[0]);
  };
  const getParamSchema = async () => {
    if (selectedOption !== '') {
      setDefaultValues({ ...defaultValues, loaded: false });
      const fetchedParams = await fetch(
        `${process.env.REACT_APP_SELECT_MODEL_ENDPOINT + selectedOption}`,
      );
      const parameterSchema = await fetchedParams.json();
      setParamSchema(parameterSchema);
      setDefaultValues({
        loaded: true,
        values: formDefaultValues.choice !== selectedOption
          ? getDefaultValues(parameterSchema)
          : formDefaultValues,
      });
    }
  };
  useEffect(() => { getOptions(paramJsonSchema.parent); }, []);
  useEffect(() => { getParamSchema(); }, [selectedOption]);
  return (
    <div key={modelName}>
      <div>
        <S.FloatingLabel className="mb-3" label={modelName}>
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

const generateTooltip = (contentStr) => (
  <OverlayTrigger
    placement="right"
    delay={{ show: 250, hide: 400 }}
    overlay={(props) => <Tooltip {...props}>{contentStr}</Tooltip>}
  >
    <button type="button">?</button>
  </OverlayTrigger>
);
const genInput = (modelName, paramJsonSchema, formik, defaultValues) => {
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
                defaultValues[parameter],
              ))
          }
        </div>
      );

    case 'integer':
      return (
        <S.InputContainerDiv key={modelName}>
          <S.FloatingLabel className="mb-3" label={modelName}>
            <S.Input
              type="number"
              name={modelName}
              value={formik.values[modelName]}
              placeholder={1}
              onChange={formik.handleChange}
              error={formik.errors[modelName]}
            />
          </S.FloatingLabel>
          {generateTooltip(paramJsonSchema.description)}
          {/* <label htmlFor="123456789"> */}
          {/*   {modelName} */}
          {/*   {generateTooltip(paramJsonSchema.description)} */}
          {/*   <br /> */}
          {/*   <input */}
          {/*     type="number" */}
          {/*     id="123456789" */}
          {/*     name={modelName} */}
          {/*     value={formik.values[modelName]} */}
          {/*     onChange={formik.handleChange} */}
          {/*     error={formik.errors[modelName]} */}
          {/*   /> */}
          {/* </label> */}
          {formik.errors[modelName]
            ? <ErrorMessageDiv>{formik.errors[modelName]}</ErrorMessageDiv>
            : null}
        </S.InputContainerDiv>
      );

    case 'string':
      return (
        <S.InputContainerDiv key={modelName}>
          <S.FloatingLabel label={modelName}>
            {/* <Select */}
            {/*   id={modelName} */}
            {/*   options={[{ value: 1, label: 'uno' }, { value: 2, label: 'dos' }]} */}
            {/**/}
            {/* /> */}
            <S.Select
              name={modelName}
              value={formik.values[modelName]}
              onChange={formik.handleChange}
              aria-label="select an option"
              error={formik.errors[modelName]}
            >
              {
                paramJsonSchema
                  .enum
                  .map((option) => <option key={option} value={option}>{option}</option>)
              }
            </S.Select>
          </S.FloatingLabel>
          {generateTooltip(paramJsonSchema.description)}
          {formik.errors[modelName]
            ? <ErrorMessageDiv>{formik.errors[modelName]}</ErrorMessageDiv>
            : null}
        </S.InputContainerDiv>
      );

    case 'number':
      return (
        <S.InputContainerDiv key={modelName}>
          <S.FloatingLabel className="mb-3" label={modelName}>
            <S.Input
              type="number"
              name={modelName}
              value={formik.values[modelName]}
              placeholder={1}
              onChange={formik.handleChange}
            />
          </S.FloatingLabel>
          {formik.errors[modelName]
            ? <ErrorMessageDiv>{formik.errors[modelName]}</ErrorMessageDiv>
            : null}
        </S.InputContainerDiv>
      );

    case 'boolean':
      return (
        <S.InputContainerDiv key={modelName}>
          <S.FloatingLabel className="mb-3" label={modelName}>
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
          {formik.errors[modelName]
            ? <ErrorMessageDiv>{formik.errors[modelName]}</ErrorMessageDiv>
            : null}
        </S.InputContainerDiv>
      );

    case 'class':
      return (
        <ClassInput
          modelName={modelName}
          paramJsonSchema={paramJsonSchema}
          setFieldValue={formik.setFieldValue}
          formDefaultValues={defaultValues}
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
    ),
  };

  SubForm.defaultProps = {
    name: 'undefined',
    defaultValues: { emptyDefaultValues: true },
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
      { genInput(name, parameterSchema, formik, defaultValues) }
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
  defaultValues,
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
    defaultValues: PropTypes.objectOf(
      PropTypes.oneOfType([
        PropTypes.string,
        PropTypes.bool,
        PropTypes.number,
        PropTypes.object,
      ]),
    ),
  };
  ParameterForm.defaultProps = {
    defaultValues: { emptyDefaultValues: true },
  };
  if (Object.keys(parameterSchema).length === 0
    || Object.prototype.hasOwnProperty.call(defaultValues, 'emptyDefaultValues')) {
    return (<div />);
  }
  const formik = useFormik({
    initialValues: defaultValues.payload,
    // initialValues: getDefaultValues(parameterSchema),
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
        { genInput(type, parameterSchema, formik, defaultValues.payload) }
      </S.Modal.Body>
      <S.Modal.Footer>
        <StyledButton onClick={formik.handleSubmit} style={{ float: 'right', width: '4rem' }}>Save</StyledButton>
        <StyledButton onClick={handleModalClose} style={{ float: 'right', width: '4rem' }}>Close</StyledButton>
      </S.Modal.Footer>
    </S.Modal>
  );
}

export default ParameterForm;
