import { ListGroup } from 'react-bootstrap';
import styled from 'styled-components';

export const StyledSection = styled.span`
  font-weight: 700;
  font-size: 20px;
`;

export const StyledNumber = styled.span`
  float: right;
  font-size: 20px;
`;

export const StyledListGroupItem = styled(ListGroup.Item)`
  background-color: ${(props) => props.theme.rootBackground};
  color: ${(props) => props.theme.title};
  border-color: ${(props) => props.theme.simpleText};
`;

export const ParameterValue = styled.span`
  color: ${(props) => props.theme.list.parameterValues};
`;
