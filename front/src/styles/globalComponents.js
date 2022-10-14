import styled from 'styled-components';
// import { styled as muiStyled } from '@mui/system';
import {
  Button,
  Card,
  FloatingLabel,
  Form,
} from 'react-bootstrap';
// import { TextField } from '@mui/material';
export const StyledButton = styled(Button)`
  background-color: ${(props) => props.theme.button.background};
  color: ${(props) => props.theme.button.text};
  &:hover {
    background-color: ${(props) => props.theme.button.backgroundHover};
  }
`;

export const Title = styled.h2`
  color: ${(props) => props.theme.title};
`;

export const SubTitle = styled.h4`
  color: ${(props) => props.theme.subTitle};
`;

export const P = styled.p`
  color: ${(props) => props.theme.simpleText};
`;

export const StyledCard = styled(Card)`
  color: ${(props) => props.theme.card.title};
  background-color: ${(props) => props.theme.card.background};
  border-color: ${(props) => props.theme.card.border};
  .card-header {
    background-color: ${(props) => props.theme.card.headerBackground};
    border-color: ${(props) => props.theme.card.headerBorder};
  }
  .card-footer {
    background-color: ${(props) => props.theme.card.footerBackground};
    border-color: ${(props) => props.theme.card.footerBorder};
  }
`;

export const StyledFloatingLabel = styled(FloatingLabel)`
   color: ${(props) => props.theme.label.text};
 `;

export const StyledTextInput = styled(Form.Control)`
 &:not(active){
   color: ${(props) => props.theme.input.text};
   background-color: ${(props) => props.theme.rootBackground};
 }
 &:focus{
   color: ${(props) => props.theme.input.text};
   background-color: ${(props) => props.theme.rootBackground};
 }
`;

export const StyledSelect = styled(Form.Select)`
  color: ${(props) => props.theme.input.text};
  background-color: ${(props) => props.theme.rootBackground};
  background-image: url("data:image/svg+xml,%3csvg xmlns=%27http://www.w3.org/2000/svg%27 viewBox=%270 0 16 16%27%3e%3cpath fill=%27white%27 stroke=%27%23white%27 stroke-linecap=%27round%27 stroke-linejoin=%27round%27 stroke-width=%272%27 d=%27m2 5 6 6 6-6%27/%3e%3c/svg%3e") !important;
  }
`;
// export const InputText = muiStyled(TextField)``;
