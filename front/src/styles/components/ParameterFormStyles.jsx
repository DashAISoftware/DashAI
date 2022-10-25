import {
  Form,
  Accordion as BootstrapAccordion,
  Modal as BootstrapModal,
  FloatingLabel as BootstrapFloatingLabel,
} from 'react-bootstrap';
import styled from 'styled-components';

export const Accordion = styled(BootstrapAccordion)`
  background-color: ${(props) => props.theme.accordion.itemBorder};
  .accordion-item {
    border-color: ${(props) => props.theme.accordion.itemBorder};
  }
  .accordion-body {
    background-color: ${(props) => props.theme.accordion.bodyBackground};
  }
`;

export const Modal = styled(BootstrapModal)`
  --bs-modal-bg: transparent;
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
export const FloatingLabel = styled(BootstrapFloatingLabel)`
  color: ${(props) => props.theme.label.text};
  text-align: left;
 `;

export const Input = styled(Form.Control)`
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

export const Select = styled(Form.Select)`
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
// TODO
export const NumberInput = null;
