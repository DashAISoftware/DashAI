import styled from 'styled-components';
import { Table } from 'react-bootstrap';

export const StyledTable = styled(Table)`
  border-color: ${(props) => props.theme.table.border};
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
`;
