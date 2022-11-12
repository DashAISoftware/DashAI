import styled from 'styled-components';
import {
  FloatingLabel as BootstrapFloatingLabel,
  Form,
} from 'react-bootstrap';

export const FloatingLabel = styled(BootstrapFloatingLabel)`
   color: ${(props) => props.theme.label.text};
   text-align: left;
 `;

export const InputText = styled(Form.Control)`
  height: 6rem !important;
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
