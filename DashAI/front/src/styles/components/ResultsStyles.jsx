import {
  ListGroup as BootstrapListGroup,
  Tabs as BootstrapTabs,
} from 'react-bootstrap';
import styled from 'styled-components';

export const SpanSection = styled.span`
  font-weight: 700;
  font-size: 20px;
`;

export const SpanNumber = styled.span`
  float: right;
  font-size: 20px;
`;

export const SpanParameterValue = styled.span`
  color: ${(props) => props.theme.list.parameterValues};
`;

export const ListGroupItem = styled(BootstrapListGroup.Item)`
  background-color: ${(props) => props.theme.rootBackground};
  color: ${(props) => props.theme.title};
  border-color: ${(props) => props.theme.simpleText};
`;

export const Tabs = styled(BootstrapTabs)`
  .nav-link {
    color: #fff;
  }
`;
