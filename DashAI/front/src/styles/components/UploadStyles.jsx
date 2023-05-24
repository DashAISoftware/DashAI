import styled from "styled-components";

export const FormFileUpload = styled.form`
  height: 16rem;
  width: 32rem;
  max-width: 100%;
  text-align: center;
  position: relative;
`;

export const LabelFileUpload = styled.label`
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  border-width: 2px;
  border-radius: 0.5rem;
  border-style: dashed;
  border-color: ${(props) => props.theme.upload.border};
  background-color: ${(props) => props.theme.rootBackground};
  &.drag-active {
    background-color: ${(props) => props.theme.upload.dragActive};
  }
  p {
    color: ${(props) => props.theme.upload.label};
  }
`;

export const DragFile = styled.div`
  position: absolute;
  width: 100%;
  height: 100%;
  border-radius: 1rem;
  top: 0px;
  right: 0px;
  bottom: 0px;
  left: 0px;
`;
