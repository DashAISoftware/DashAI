import React, { useState } from "react";
import { Card, Form } from "react-bootstrap";
import {
  StyledButton,
  Loading,
  StyledCard,
  P,
} from "../styles/globalComponents";
import * as S from "../styles/components/PlayStyles";
import { getPrediction as getPredictionRequest } from "../api/oldEndpoints";

function Play() {
  const sessionId = 0;
  const executionId = 0;

  const [modelPrediction, setModelPrediction] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    setModelPrediction("null");
    const data = Object.fromEntries(Array.from(new FormData(e.target)));

    try {
      const prediction = await getPredictionRequest(
        sessionId,
        executionId,
        data.modelInput,
      );
      setModelPrediction(prediction);
    } catch (error) {
      console.error(error);
    }
  };

  return (
    <StyledCard style={{ width: "32rem", textAlign: "left" }}>
      <Card.Header>Play with the model</Card.Header>
      <Form style={{ margin: "10px" }} onSubmit={handleSubmit}>
        <P>Enter input for the model</P>
        <S.FloatingLabel label="Input" className="mb-3">
          <S.InputText
            className="form-control"
            as="textarea"
            name="modelInput"
          />
        </S.FloatingLabel>
        <StyledButton
          type="submit"
          variant="dark"
          style={{ float: "right", marginRight: "3px" }}
        >
          Send
        </StyledButton>
      </Form>
      <StyledCard className="text-center" style={{ margin: "1rem" }}>
        <Card.Title style={{ margin: "20px" }}>
          {modelPrediction === "null" ? (
            <Loading alt="" src="/images/loading.png" width="29" height="29" />
          ) : (
            <Card.Title style={{ margin: "20px" }}>
              {modelPrediction}
            </Card.Title>
          )}
        </Card.Title>
      </StyledCard>
    </StyledCard>
  );
}

export default Play;