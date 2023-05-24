import styled from "styled-components";

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
