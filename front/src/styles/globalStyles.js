import { createGlobalStyle } from 'styled-components';
import theme from './theme';

const GlobalStyle = createGlobalStyle`
  body {
    background-color: ${theme.rootBackground};
  }

`;

export default GlobalStyle;
