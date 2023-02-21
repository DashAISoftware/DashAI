import {
  Modal as BootstrapModal,
} from 'react-bootstrap';
import styled from 'styled-components';

export const Modal = styled(BootstrapModal)`
  --bs-modal-bg: transparent;
  .modal-header {
    background-color: ${(props) => props.theme.card.background};
    border-color: ${(props) => props.theme.card.background};
    text-align: center;
    display: block;
    padding-top: 25px;
  }
  .modal-body {
    color: ${(props) => props.theme.card.title};
    background-color: ${(props) => props.theme.card.background};
    padding: 0px 50px;
  }
  .modal-footer {
    background-color: ${(props) => props.theme.card.background};
    border-color: ${(props) => props.theme.card.background};
    padding-right: 50px;
    padding-bottom: 25px;
  }
`;
export const TextInput = styled.input`
  background-color: ${(props) => props.theme.card.background};
  outline: ${(props) => props.theme.table.border};
  color: ${(props) => props.theme.simpleText};
  border-radius: 10px;
  margin-bottom: 15px;
  padding: 2px 45px;
  &:focus {
    border-color: ${(props) => props.theme.button.background};
  }
`;
export const HiddenSection = styled.div`
  overflow: hidden;
  max-height: 0;
  transition: max-height 0.3s ease-in-out;
`;
