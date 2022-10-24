import React, { useState } from 'react';
import {
  Card,
  // Spinner,
  Form,
  FloatingLabel,
} from 'react-bootstrap';
import styled from 'styled-components';
import {
  StyledButton,
  // StyledFloatingLabel,
  // StyledTextInput,
  StyledCard,
  P,
} from '../styles/globalComponents';

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

const Loading = styled.img`
  @keyframes spin {
    from {transform:rotate(0deg);}
    to {transform:rotate(360deg);}
  }
  animation: spin 3s linear infinite;
`;

function Play() {
  const sessionId = 0;
  const [modelPrediction, setModelPrediction] = useState('');
  const handleSubmit = async (e) => {
    e.preventDefault();
    setModelPrediction('null');
    const data = Object.fromEntries(Array.from(new FormData(e.target)));
    const fetchedPrediction = await fetch(
      `${process.env.REACT_APP_PLAY_ENDPOINT + sessionId}/0/{input}?input_data=${data.modelInput}`,
    );
    const prediction = await fetchedPrediction.json();
    setModelPrediction(prediction);
  };
  return (
    <StyledCard style={{ width: '32rem', textAlign: 'left' }}>
      <Card.Header>Play with the model</Card.Header>
      <Form style={{ margin: '10px' }} onSubmit={handleSubmit}>
        <P>Enter input for the model</P>
        <StyledFloatingLabel label="Input" className="mb-3">
          <StyledTextInput className="form-control" as="textarea" name="modelInput" style={{ height: '6rem' }} />
        </StyledFloatingLabel>
        <StyledButton
          type="submit"
          variant="dark"
          style={{ float: 'right', marginRight: '3px' }}
        >
          Send
        </StyledButton>
      </Form>
      <StyledCard className="text-center" style={{ margin: '1rem' }}>
        <Card.Title style={{ margin: '20px' }}>
          {
          modelPrediction === 'null'
            ? <Loading alt="" src="images/loading.png" width="29" height="29" />
            : <Card.Title style={{ margin: '20px' }}>{modelPrediction}</Card.Title>
          }
        </Card.Title>
      </StyledCard>
    </StyledCard>
  );
}

export default Play;
