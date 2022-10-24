import React, { useState, useEffect, useRef } from 'react';
import {
  Accordion,
  Form,
  FloatingLabel,
  // Dropdown,
  // Card,
  Modal,
} from 'react-bootstrap';
import PropTypes from 'prop-types';
import styled from 'styled-components';
import { useFormik } from 'formik';
import {
  P,
  // StyledFloatingLabel,
  // StyledTextInput,
  // StyledSelect,
  StyledButton,
  // StyledCard,
} from '../styles/globalComponents';
import { getDefaultValues } from '../utils/values';
import { StyledAccordion } from '../styles/components/ParameterFormStyles';

const StyledModal = styled(Modal)`
  .modal-header {
    background-color: ${(props) => props.theme.card.headerBackground};
    border-color: ${(props) => props.theme.card.headerBorder};
  }
  .modal-body {
    color: ${(props) => props.theme.card.title};
    background-color: ${(props) => props.theme.card.background};
  }
  .modal-footer {
    background-color: ${(props) => props.theme.card.footerBackground};
    border-color: ${(props) => props.theme.card.footerBorder};
  }
`;
const StyledFloatingLabel = styled(FloatingLabel)`
   color: ${(props) => props.theme.label.text};
   text-align: left;
 `;

const StyledTextInput = styled(Form.Control)`
  border-color: ${(props) => props.theme.input.border};
  &:not(active){
    color: ${(props) => props.theme.input.text};
    background-color: ${(props) => props.theme.rootBackground};
  }
  &:focus{
    color: ${(props) => props.theme.input.text};
    background-color: ${(props) => props.theme.rootBackground};
    border-color: ${(props) => props.theme.input.borderFocus};
    box-shadow: none;
  }
`;
const StyledSelect = styled(Form.Select)`
  color: ${(props) => props.theme.input.text};
  border-color: ${(props) => props.theme.input.border};
  background-color: ${(props) => props.theme.rootBackground};
  border-radius: 6px;
  position: relative;
  background-image: url("data:image/svg+xml,%3csvg xmlns=%27http://www.w3.org/2000/svg%27 viewBox=%270 0 16 16%27%3e%3cpath fill=%27white%27 stroke=%27%23white%27 stroke-linecap=%27round%27 stroke-linejoin=%27round%27 stroke-width=%272%27 d=%27m2 5 6 6 6-6%27/%3e%3c/svg%3e") !important;
  &:focus {
    border: 1px solid #05abbb;
    box-shadow: none;
    border-color: ${(props) => props.theme.input.borderFocus};
  }
`;
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
    <div key={modelName}>
      <div>
        <StyledFloatingLabel className="mb-3" label={modelName} style={{ display: 'inline-block', width: '90%' }}>
          <StyledSelect
            value={selectedOption}
            name="choice"
            onChange={(e) => setSelectedOption(e.target.value)}
          >
            {options.map((option) => <option key={option}>{option}</option>)}
          </StyledSelect>
        </StyledFloatingLabel>
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
      <StyledAccordion ref={accordionRef} style={{ marginTop: '-0.5rem', marginBottom: '1rem', width: '90%' }}>
        <Accordion.Item eventKey="0">
          <Accordion.Header style={{ display: 'none' }}>{`${selectedOption} parameters`}</Accordion.Header>
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
      </StyledAccordion>
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
          <StyledFloatingLabel className="mb-3" label={modelName} style={{ width: '90%' }}>
            <StyledTextInput
              type="number"
              name={modelName}
              value={formik.values[modelName]}
              placeholder={1}
              onChange={formik.handleChange}
            />
          </StyledFloatingLabel>
        </div>
      );

    case 'string':
      return (
        <div key={modelName}>
          <StyledFloatingLabel className="mb-3" label={modelName} style={{ width: '90%' }}>
            <StyledSelect
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
            </StyledSelect>
          </StyledFloatingLabel>
        </div>
      );

    case 'number':
      return (
        <div key={modelName}>
          <StyledFloatingLabel className="mb-3" label={modelName} style={{ width: '90%' }}>
            <StyledTextInput
              type="number"
              name={modelName}
              value={formik.values[modelName]}
              placeholder={1}
              onChange={formik.handleChange}
            />
          </StyledFloatingLabel>
        </div>
      );

    case 'boolean':
      return (
        <div key={modelName}>
          <StyledFloatingLabel className="mb-3" label={modelName} style={{ width: '90%' }}>
            <StyledSelect
              name={modelName}
              value={formik.values[modelName]}
              onChange={formik.handleChange}
              aria-label="select an option"
            >
              <option key={`${modelName}-true`} value="True">True</option>
              <option key={`${modelName}-false`} value="False">False</option>
            </StyledSelect>
          </StyledFloatingLabel>
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
    modalShow: PropTypes.string.isRequired,
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
    <StyledModal show={modalShow} onHide={handleClose}>
      <Modal.Header>
        <P>Model parameters</P>
      </Modal.Header>
      <Modal.Body style={{ padding: '0px 10px' }}>
        <br />
        { genInput(type, parameterSchema, formik) }
      </Modal.Body>
      <Modal.Footer>
        <StyledButton onClick={formik.handleSubmit} style={{ float: 'right', width: '4rem' }}>Save</StyledButton>
        <StyledButton onClick={handleClose} style={{ float: 'right', width: '4rem' }}>Close</StyledButton>
      </Modal.Footer>
    </StyledModal>
  );
}

export default ParameterForm;
