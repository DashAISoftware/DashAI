import { Accordion } from 'react-bootstrap';
import styled from 'styled-components';

export const StyledAccordion = styled(Accordion)`
  background-color: ${(props) => props.theme.accordion.itemBorder};
  .accordion-item {
    border-color: ${(props) => props.theme.accordion.itemBorder};
  }
  .accordion-body {
    background-color: ${(props) => props.theme.accordion.bodyBackground};
  }
`;

// TODO
export const NumberInput = null;
