import styled from "styled-components";
import { Form } from "react-bootstrap";
import { StyledButton } from "../globalComponents";

export const FormFileUpload = styled(Form)`
  height: 16rem;
  width: 30rem;
  text-align: center;
  position: relative;
`;

export const LabelFileUpload = styled.label`
  height: 100%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  border-width: 2px;
  border-radius: 0.5rem;
  border-style: dashed;
  border-color: ${(props) => props.theme.upload.border};
  background-color: #121212;
  &.drag-active {
    background-color: ${(props) => props.theme.upload.dragActive};
  }
  p {
    color: ${(props) => props.theme.upload.label};
  }
`;

export const UploadButton = styled(StyledButton)`
  cursor: pointer;
  position: relative;
  padding: 0.25rem;
  font-size: 1rem;
  border: none;
`;

export const DragFile = styled.div`
  position: absolute;
  width: 100%;
  height: 100%;
  border-radius: 1rem;
  top: 0px;
  right: 0px;
  bottom: 0px;
  left: 0px;
`;
