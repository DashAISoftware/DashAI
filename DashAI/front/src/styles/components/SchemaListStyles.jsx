import { Modal as BootstrapModal } from "react-bootstrap";
import styled from "styled-components";
import { Table as muiTable } from "@mui/material";
import { styled as muiStyled } from "@mui/material/styles";

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
  .modal-dialog {
    max-width: 1000px;
  }
`;
export const NameModal = styled(BootstrapModal)`
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
export const InfoPanel = muiStyled("div")({
  backgroundColor: "#24262b",
  borderRadius: "6px",
  padding: "20px 15px",
  height: "300px",
  textAlign: "justify",
  overflowY: "scroll",
});

export const SearchBar = muiStyled("div")({
  backgroundColor: "transparent",
  outline: "#fff",
  color: "#fff",
  borderRadius: "6px",
  marginBottom: "10px",
  padding: "2px 45px",
});

export const Table = muiStyled(muiTable)({
  borderRadius: "6px",
});

export const TableWrapper = muiStyled("div")({
  maxHeight: "300px",
  overflowY: "scroll",
});

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
