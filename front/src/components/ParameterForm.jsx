import React from 'react';
import {
  Form,
  DropdownButton,
  InputGroup,
  Dropdown,
  Card,
  Button,
} from 'react-bootstrap';
import PropTypes from 'prop-types';
import uuid from 'react-uuid';

// const fakeData = {
//   type: 'object',
//   properties: {
//     a: {
//       oneOf: [
//         {
//           type: 'integer',
//           default: 5,
//           minimum: 1,
//         },
//       ],
//     },
//     b: {
//       oneOf: [
//         {
//           type: 'string',
//           default: 'uniform',
//           enum: ['uniform', 'distance'],
//         },
//       ],
//     },
//   },
// };

function ParameterForm({ model, parameterSchema }) {
  ParameterForm.propTypes = {
    model: PropTypes.string.isRequired,
    parameterSchema: PropTypes.objectOf(
      PropTypes.oneOfType([
        PropTypes.string,
        PropTypes.bool,
        PropTypes.object,
      ]),
    ).isRequired,
  };
  const genInput = (modelName, paramJsonSchema) => {
    const { type, properties } = paramJsonSchema;
    switch (type) {
      case 'object':
        return (
          <div>
            {
              Object.keys(properties)
                .map((parameter) => genInput(parameter, properties[parameter].oneOf[0]))
            }
          </div>
        );

      case 'integer':
        return (
          <InputGroup key={uuid()} className="mb-3">
            <InputGroup.Text style={{ width: '150px' }}>{modelName}</InputGroup.Text>
            <input type="number" style={{ borderRadius: '5px', width: '165px' }} />
          </InputGroup>
        );

      case 'string':
        return (
          <DropdownButton key={uuid()} className="mb-3" title="Select" variant="secondary">
            {
              paramJsonSchema
                .enum
                .map((option) => <Dropdown.Item key={option}>{option}</Dropdown.Item>)
            }
          </DropdownButton>
        );

      case 'class':
        return (
          <InputGroup key={uuid()} className="mb-3">
            <InputGroup.Text style={{ width: '150px' }}>{modelName}</InputGroup.Text>
            <DropdownButton key={uuid()} className="mb-3" title="This is a recursion">
              <Dropdown.Item>{paramJsonSchema.parent}</Dropdown.Item>
            </DropdownButton>
          </InputGroup>
        );

      default:
        return (
          <p key={type} style={{ color: 'red', fontWeight: 'bold' }}>{`Not a valid parameter type: ${type}`}</p>
        );
    }
  };
  return (
    <Card style={{ width: '25rem' }}>
      <Card.Header>Model parameters</Card.Header>
      <Form style={{ padding: '40px 10px' }}>
        { genInput(model, parameterSchema) }
      </Form>
      <Card.Footer>
        <Button variant="dark" style={{ width: '100%' }}>Save</Button>
      </Card.Footer>
    </Card>
  );
}

export default ParameterForm;
