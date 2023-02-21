import styled from 'styled-components';
import {
  Button,
  Card,
  FloatingLabel,
  Form,
} from 'react-bootstrap';

export const StyledButton = styled(Button)`
  background-color: ${(props) => props.theme.button.background};
  color: ${(props) => props.theme.button.text};
  height: 2.2rem;
  border-color: ${(props) => props.theme.button.border};
  &:hover {
    background-color: ${(props) => props.theme.button.backgroundHover};
    color: ${(props) => props.theme.button.textHover};
    border-color: ${(props) => props.theme.button.borderHover};
  }
  &:focus {
    background-color: ${(props) => props.theme.button.backgroundFocus};
    color: ${(props) => props.theme.button.textFocus};
    box-shadow: none;
  }
`;

export const Title = styled.h2`
  color: ${(props) => props.theme.title};
  font-weight: 700;
  font-size: 40px;
  font-height: 50px;
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
   text-align: left;
   &.form-floating>label {
     padding-left: 34px;
     padding-top: 1.4rem;
   }
 `;

export const StyledTextInput = styled(Form.Control)`
  border-color: ${(props) => props.theme.input.border};
  width: 15.9rem;
  height: 4.4rem !important;
  padding-left: 34px !important;
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

export const StyledSelect = styled(Form.Select)`
  color: ${(props) => props.theme.input.text};
  border-color: ${(props) => props.theme.input.border};
  background-color: ${(props) => props.theme.rootBackground};
  border-radius: 6px;
  min-width: 15.9rem;
  height: 4.4rem !important;
  padding-left: 34px;
  position: relative;
  background-image: url("data:image/svg+xml,%3csvg xmlns=%27http://www.w3.org/2000/svg%27 viewBox=%270 0 16 16%27%3e%3cpath fill=%27white%27 stroke=%27%23white%27 stroke-linecap=%27round%27 stroke-linejoin=%27round%27 stroke-width=%272%27 d=%27m2 5 6 6 6-6%27/%3e%3c/svg%3e") !important;
  &:focus {
    border: 1px solid #05abbb;
    box-shadow: none;
    border-color: ${(props) => props.theme.input.borderFocus};
  }
`;

export const Loading = styled.img`
  @keyframes spin {
    from {transform:rotate(0deg);}
    to {transform:rotate(360deg);}
  }
  animation: spin 3s linear infinite;
`;

export const ErrorMessageDiv = styled.div`
  color: ${(props) => props.theme.input.borderError};
  margin-top: -0.9rem;
  font-size: 0.85rem;
`;

export const CustomContainer = styled.div`
  height: 89vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  justify-content: center;
`;
