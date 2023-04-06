/* eslint-disable react/jsx-props-no-spreading */
import React, { useState, useEffect, useRef } from "react";
import InputLabel from "@mui/material/InputLabel";
import MenuItem from "@mui/material/MenuItem";
import FormControl from "@mui/material/FormControl";
import Select from "@mui/material/Select";
import PropTypes from "prop-types";
import { useFormik } from "formik";
import * as Yup from "yup";
import { Tooltip, IconButton } from "@mui/material";
import HelpOutlineIcon from "@mui/icons-material/HelpOutline";
// import OverlayTrigger from "react-bootstrap/OverlayTrigger";
// import Tooltip from "react-bootstrap/Tooltip";
// import Select from 'react-select';
import { P, StyledButton, ErrorMessageDiv } from "../styles/globalComponents";
import { getDefaultValues } from "../utils/values";
import * as S from "../styles/components/ParameterFormStyles";

function genYupValidation(yupInitialObj, schema) {
  let finalObj = yupInitialObj;
  if ("maximum" in schema) {
    finalObj = finalObj.max(schema.maximum, schema.error_msg);
  }
  if ("minimum" in schema) {
    finalObj = finalObj.min(schema.minimum, schema.error_msg);
  }
  if ("exclusiveMinimum" in schema) {
    finalObj = finalObj.min(
      Math.min(schema.exclusiveMinimum, schema.default),
      schema.error_msg
    );
  }

  if ("enum" in schema) {
    finalObj = finalObj.oneOf(schema.enum);
  }
  if ("optional" in schema) {
    return finalObj;
  }
  return finalObj.required("Required");
}

function getValidation(parameterJsonSchema) {
  const { properties } = parameterJsonSchema;
  const validationObject = {};
  if (typeof properties !== "undefined") {
    const parameters = Object.keys(properties);
    parameters.forEach((param) => {
      const subSchema = properties[param].oneOf[0];
      let yupInitialObj = null;
      switch (subSchema.type) {
        case "integer":
          yupInitialObj = Yup.number().integer();
          break;
        case "number":
          yupInitialObj = Yup.number();
          break;
        case "float":
          yupInitialObj = Yup.number();
          break;
        case "string":
          yupInitialObj = Yup.string();
          break;
        case "text":
          yupInitialObj = Yup.string();
          break;
        case "boolean":
          yupInitialObj = Yup.boolean();
          break;
        default:
          yupInitialObj = "none";
      }
      if (yupInitialObj !== "none") {
        validationObject[param] = genYupValidation(yupInitialObj, subSchema);
      }
    });
  }
  return Yup.object().shape(validationObject);
}

// export const generateTooltip = (contentStr) => (
//   <OverlayTrigger
//     placement="right"
//     delay={{ show: 250, hide: 400 }}
//     overlay={(props) => <Tooltip {...props}>{contentStr}</Tooltip>}
//   >
//     <S.TooltipButton type="button">
//       <p>?</p>
//     </S.TooltipButton>
//   </OverlayTrigger>
// );

export const generateTooltip = (contentStr) => (
  <Tooltip
    title={<div dangerouslySetInnerHTML={{ __html: contentStr }} />}
    placement="right-start"
    arrow
  >
    <IconButton>
      <HelpOutlineIcon />
    </IconButton>
  </Tooltip>
);

function ClassInput({
  modelName,
  paramJsonSchema,
  setFieldValue,
  formDefaultValues,
}) {
  ClassInput.propTypes = {
    modelName: PropTypes.string.isRequired,
    paramJsonSchema: PropTypes.objectOf(
      PropTypes.oneOfType([PropTypes.string, PropTypes.bool, PropTypes.object])
    ).isRequired,
    setFieldValue: PropTypes.func.isRequired,
    formDefaultValues: PropTypes.objectOf(
      PropTypes.oneOfType([
        PropTypes.string,
        PropTypes.bool,
        PropTypes.number,
        PropTypes.object,
      ])
    ),
  };
  ClassInput.defaultProps = {
    formDefaultValues: { emptyDefaultValues: true },
  };
  const [options, setOptions] = useState([]);
  const [selectedOption, setSelectedOption] = useState(
    formDefaultValues.choice
  );
  const [paramSchema, setParamSchema] = useState({});
  const [defaultValues, setDefaultValues] = useState({
    loaded: true,
    values: formDefaultValues,
  });
  const accordionRef = useRef(null);
  const handleButtonClick = () => {
    accordionRef.current.childNodes[0].childNodes[0].childNodes[0].click();
  };
  const getOptions = async (parentClass) => {
    const fetchedOptions = await fetch(
      `${process.env.REACT_APP_GET_CHILDREN_ENDPOINT + parentClass}`
    );
    const receivedOptions = await fetchedOptions.json();
    setOptions(receivedOptions);
    // setSelectedOption(receivedOptions[0]);
  };
  const getParamSchema = async () => {
    if (selectedOption !== "") {
      setDefaultValues({ ...defaultValues, loaded: false });
      const fetchedParams = await fetch(
        `${process.env.REACT_APP_SELECT_MODEL_ENDPOINT + selectedOption}`
      );
      const parameterSchema = await fetchedParams.json();
      setParamSchema(parameterSchema);
      setDefaultValues({
        loaded: true,
        values:
          formDefaultValues.choice !== selectedOption
            ? getDefaultValues(parameterSchema)
            : formDefaultValues,
      });
    }
  };
  useEffect(() => {
    getOptions(paramJsonSchema.parent);
  }, []);
  useEffect(() => {
    getParamSchema();
  }, [selectedOption]);
  return (
    <div key={modelName}>
      <div>
        <S.FloatingLabel className="mb-3" label={modelName}>
          <S.Select
            value={selectedOption}
            name="choice"
            onChange={(e) => setSelectedOption(e.target.value)}
          >
            {options.map((option) => (
              <option key={option}>{option}</option>
            ))}
          </S.Select>
        </S.FloatingLabel>
        {generateTooltip(paramJsonSchema.description)}
        <StyledButton
          type="button"
          style={{
            display: "inline-block",
            marginLeft: "0.5rem",
            marginBottom: "1.5rem",
            width: "2.5rem",
          }}
          onClick={handleButtonClick}
        >
          <img
            alt=""
            style={{ marginBottom: "0.2rem" }}
            src="/images/settings.svg"
            width="16"
            height="16"
          />
        </StyledButton>
      </div>
      <S.Accordion
        ref={accordionRef}
        style={{ marginTop: "-0.5rem", marginBottom: "1rem", width: "80%" }}
      >
        <S.Accordion.Item eventKey="0">
          <S.Accordion.Header
            style={{ display: "none" }}
          >{`${selectedOption} parameters`}</S.Accordion.Header>
          <S.Accordion.Body key={selectedOption}>
            {defaultValues.loaded && (
              <SubForm
                name={modelName}
                parameterSchema={paramSchema}
                setFieldValue={setFieldValue}
                choice={selectedOption}
                defaultValues={defaultValues.values}
              />
            )}
          </S.Accordion.Body>
        </S.Accordion.Item>
      </S.Accordion>
    </div>
  );
}

const genInput = (modelName, paramJsonSchema, formik, defaultValues) => {
  const { type, properties } = paramJsonSchema;
  switch (type) {
    case "object":
      return (
        <div key={modelName}>
          {Object.keys(properties).map((parameter) =>
            genInput(
              parameter,
              properties[parameter].oneOf[0],
              formik,
              defaultValues[parameter]
            )
          )}
        </div>
      );
    case "integer":
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
          {formik.errors[modelName] ? (
            <ErrorMessageDiv>{formik.errors[modelName]}</ErrorMessageDiv>
          ) : null}
        </S.InputContainerDiv>
      );

    case "number":
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
          {generateTooltip(paramJsonSchema.description)}
          {formik.errors[modelName] ? (
            <ErrorMessageDiv>{formik.errors[modelName]}</ErrorMessageDiv>
          ) : null}
        </S.InputContainerDiv>
      );

    case "float":
      return (
        <S.InputContainerDiv key={modelName}>
          <S.FloatingLabel className="mb-3" label={modelName}>
            <S.Input
              type="number"
              step="0.01"
              lang="en"
              pattern="/^[0-9]*\.?[0-9]*$/"
              name={modelName}
              value={formik.values[modelName]}
              placeholder={0.1}
              onChange={formik.handleChange}
            />
          </S.FloatingLabel>
          {generateTooltip(paramJsonSchema.description)}
          {formik.errors[modelName] ? (
            <ErrorMessageDiv>{formik.errors[modelName]}</ErrorMessageDiv>
          ) : null}
        </S.InputContainerDiv>
      );
    case "string":
      return (
        <S.InputContainerDiv key={modelName}>
          <FormControl fullWidth>
            <InputLabel id={`demo-simple-select-label-${modelName}`}>
              {modelName}
            </InputLabel>
            <Select
              labelId={`demo-simple-select-label-${modelName}`}
              value={formik.values[modelName]}
              label={modelName}
              onChange={formik.handleChange}
              error={formik.errors[modelName]}
            >
              {paramJsonSchema.enum.map((option) => (
                <MenuItem key={option} value={option}>
                  {option}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
          {generateTooltip(paramJsonSchema.description)}
          {formik.errors[modelName] ? (
            <ErrorMessageDiv>{formik.errors[modelName]}</ErrorMessageDiv>
          ) : null}
        </S.InputContainerDiv>
      );
    case "text":
      return (
        <S.InputContainerDiv key={modelName}>
          <S.FloatingLabel className="mb-3" label={modelName}>
            <S.Input
              type="text"
              name={modelName}
              value={formik.values[modelName]}
              onChange={formik.handleChange}
              error={formik.errors[modelName]}
            />
          </S.FloatingLabel>
          {generateTooltip(paramJsonSchema.description)}
          {formik.errors[modelName] ? (
            <ErrorMessageDiv>{formik.errors[modelName]}</ErrorMessageDiv>
          ) : null}
        </S.InputContainerDiv>
      );
    case "boolean":
      return (
        <S.InputContainerDiv key={modelName}>
          <S.FloatingLabel className="mb-3" label={modelName}>
            <S.Select
              name={modelName}
              value={formik.values[modelName]}
              onChange={formik.handleChange}
              aria-label="select an option"
            >
              {defaultValues === false ? (
                <>
                  <option key={`${modelName}-false`} value="False">
                    False
                  </option>
                  <option key={`${modelName}-true`} value="True">
                    True
                  </option>
                </>
              ) : (
                <>
                  <option key={`${modelName}-true`} value="True">
                    True
                  </option>
                  <option key={`${modelName}-false`} value="False">
                    False
                  </option>
                </>
              )}
            </S.Select>
          </S.FloatingLabel>
          {generateTooltip(paramJsonSchema.description)}
          {formik.errors[modelName] ? (
            <ErrorMessageDiv>{formik.errors[modelName]}</ErrorMessageDiv>
          ) : null}
        </S.InputContainerDiv>
      );

    case "class":
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
        <p
          style={{ color: "red", fontWeight: "bold" }}
        >{`Not a valid parameter type: ${type}`}</p>
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
      PropTypes.oneOfType([PropTypes.string, PropTypes.bool, PropTypes.object])
    ).isRequired,
    setFieldValue: PropTypes.func.isRequired,
    choice: PropTypes.string.isRequired,
    defaultValues: PropTypes.objectOf(
      PropTypes.oneOfType([
        PropTypes.string,
        PropTypes.number,
        PropTypes.bool,
        PropTypes.object,
      ])
    ),
  };

  SubForm.defaultProps = {
    name: "undefined",
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
      {genInput(name, parameterSchema, formik, defaultValues)}
    </div>
  );
}

function ParameterForm({
  type,
  parameterSchema,
  handleFormSubmit,
  showModal,
  handleModalClose,
  defaultValues,
  extraOptions, // to add specifics sections
  backdrop, // added to handle that not close the modal when clicking out of it
  noClose, // to not have the close button
  handleBack, // to have or not a back button
  getValues, // to obtain the current value of an input
}) {
  ParameterForm.propTypes = {
    type: PropTypes.string.isRequired,
    parameterSchema: PropTypes.objectOf(
      PropTypes.oneOfType([PropTypes.string, PropTypes.bool, PropTypes.object])
    ).isRequired,
    handleFormSubmit: PropTypes.func.isRequired,
    showModal: PropTypes.bool.isRequired,
    handleModalClose: PropTypes.func.isRequired,
    defaultValues: PropTypes.objectOf(
      PropTypes.oneOfType([
        PropTypes.string,
        PropTypes.bool,
        PropTypes.number,
        PropTypes.object,
      ])
    ),
    extraOptions: PropTypes.shape({}),
    backdrop: PropTypes.string,
    noClose: PropTypes.bool,
    handleBack: PropTypes.func,
    getValues: PropTypes.arrayOf(
      PropTypes.shape({
        inputName: PropTypes.string,
        setValue: PropTypes.func,
      })
    ),
  };
  const formik = useFormik({
    initialValues: defaultValues?.payload ?? {},
    // initialValues: getDefaultValues(parameterSchema),
    validationSchema: getValidation(parameterSchema),
    onSubmit: (values) => {
      handleFormSubmit(type, values);
      handleModalClose();
    },
  });
  useEffect(() => {
    // get current values of an input
    if (getValues !== null && typeof getValues !== "undefined") {
      getValues[1](formik.values[getValues[0]]);
    }
  }, [formik.values]);
  if (
    Object.keys(parameterSchema).length === 0 ||
    "emptyDefaultValues" in defaultValues
  ) {
    return <div />;
  }
  if (parameterSchema.display === "div") {
    // return the inputs in a div
    return (
      // here don't exist a submit button so we to need obtain the data with onChange method
      <div onChange={formik.handleSubmit}>
        {genInput(type, parameterSchema, formik, defaultValues.payload)}
      </div>
    );
  }
  if (
    parameterSchema.display === "modal" ||
    parameterSchema.display === undefined
  ) {
    return (
      <S.Modal backdrop={backdrop} show={showModal} onHide={handleModalClose}>
        <S.Modal.Header>
          {handleBack !== null ? (
            <button
              type="button"
              className="bg-transparent"
              onClick={handleBack}
              style={{ float: "left", border: "none" }}
            >
              <img alt="" src="/images/back.svg" width="30" height="30" />
            </button>
          ) : null}
          <P style={{ marginTop: "0.8rem" }}>{`${type} parameters`}</P>
          {noClose ? (
            <div style={{ width: "180px" }} />
          ) : (
            <button
              type="button"
              className="bg-transparent"
              onClick={handleModalClose}
              style={{ float: "right", border: "none" }}
            >
              <img alt="" src="/images/close.svg" width="40" height="40" />
            </button>
          )}
        </S.Modal.Header>
        <S.Modal.Body style={{ padding: "0px 10px" }}>
          <br />
          {genInput(type, parameterSchema, formik, defaultValues.payload)}
          {extraOptions}
        </S.Modal.Body>
        <S.Modal.Footer>
          <StyledButton onClick={formik.handleSubmit} style={{ width: "25%" }}>
            Save
          </StyledButton>
        </S.Modal.Footer>
      </S.Modal>
    );
  }
}

ParameterForm.defaultProps = {
  defaultValues: { emptyDefaultValues: true },
  extraOptions: null,
  backdrop: "true",
  noClose: false,
  handleBack: null,
  getValues: null,
};

export default ParameterForm;
