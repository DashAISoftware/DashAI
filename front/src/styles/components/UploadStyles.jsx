import styled from 'styled-components';
import { Form } from 'react-bootstrap';
import { StyledButton } from '../globalComponents';

export const FormFileUpload = styled(Form)`
  height: 10rem;
  width: 28rem;
  max-width: 100%;
  text-align: center;
  position: relative;
`;

export const LabelFileUpload = styled.label`
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  border-width: 2px;
  border-radius: 0.5rem;
  border-style: dashed;
  border-color: #cbd5e1;
  background-color: ${(props) => props.theme.rootBackground};
  &.drag-active {
    background-color: #1e1f24;
  }
  p {
    color: ${(props) => props.theme.uploadLabel};
  }
`;

export const UploadButton = styled(StyledButton)`
  cursor: pointer;
  margin-top: 4rem;
  position: absolute;
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
