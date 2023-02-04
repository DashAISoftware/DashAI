import {
  Table as BootstrapTable,
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
export const SearchBar = styled.input`
  background-color: ${(props) => props.theme.card.background};
  outline: ${(props) => props.theme.table.border};
  color: ${(props) => props.theme.simpleText};
  border-radius: 10px;
  margin-bottom: 15px;
  padding: 2px 45px;
  background: transparent url('images/search.svg') no-repeat 8px center;
  &:focus {
    border-color: ${(props) => props.theme.button.background};
  }
`;

export const Table = styled(BootstrapTable)`
  border-color: ${(props) => props.theme.table.border};
  border-radius: 6px;
`;

export const Th = styled.th`
  color: ${(props) => props.theme.table.header};
  margin-left: 100px !important;
`;

export const Td = styled.td`
  color: ${(props) => props.theme.table.data};
`;

export const Tr = styled.tr`
  text-align: left;
  &:hover {
    background-color: #282a30;
    td {
      color: ${(props) => props.theme.table.data} !important;
    }
  }
`;
