import styled from "styled-components";

export const Title = styled.h2`
  color: ${(props) => props.theme.title};
  font-weight: 700;
  font-size: 40px;
  font-height: 50px;
`;

export const SubTitle = styled.h4`
  color: ${(props) => props.theme.subTitle};
`;

export const P = styled.p`
  color: ${(props) => props.theme.simpleText};
`;

export const Loading = styled.img`
  @keyframes spin {
    from {
      transform: rotate(0deg);
    }
    to {
      transform: rotate(360deg);
    }
  }
  animation: spin 3s linear infinite;
`;

export const ErrorMessageDiv = styled.div`
  color: ${(props) => props.theme.input.borderError};
  padding-top: 15px;
  margin-top: -0.9rem;
  font-size: 0.85rem;
`;
