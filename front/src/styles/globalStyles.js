import { createGlobalStyle } from 'styled-components';
import theme from './theme';
import QuicksandRegular from './fonts/Quicksand-Regular.ttf';
// import QuicksandBold from './fonts/Quicksand-Bold.ttf';

const GlobalStyle = createGlobalStyle`
  html {
    overflow: auto;
  }
  body {
    background-color: ${theme.rootBackground};
  }
  ::-webkit-scrollbar {
    width: 12px;
  }

  @font-face {
    font-family: 'Quicksand';
    src: url(${QuicksandRegular});
  }
  /* Track */
  ::-webkit-scrollbar-track {
      -webkit-box-shadow: inset 0 0 6px rgba(0,0,0,0.3); 
      -webkit-border-radius: 10px;
      border-radius: 10px;
  }
   
  /* Handle */
  ::-webkit-scrollbar-thumb {
      -webkit-border-radius: 10px;
      border-radius: 10px;
      background: rgba(0,0,0,0.8); 
      -webkit-box-shadow: inset 0 0 6px rgba(0,0,0,0.5); 
  }
  ::-webkit-scrollbar-thumb:window-inactive {
          background: rgba(0,0,0,0.4); 
  }
`;

export default GlobalStyle;
