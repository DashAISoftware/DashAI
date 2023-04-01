import styled from "styled-components";
import { Table as BootstrapTable } from "react-bootstrap";

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
