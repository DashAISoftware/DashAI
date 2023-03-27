import QuicksandBoldWoff2 from './fonts/Quicksand-Bold.woff2';

const muiGlobalStyle = {
  palette: {
    background: {
      default: '#2e3037',
    },
    text: {
      primary: '#ffffff',
    },
  },
  typography: {
    fontFamily: [
      '-apple-system',
      'BlinkMacSystemFont',
      'Quicksand-Bold',
      '"Segoe UI"',
      'Roboto',
      'Oxygen',
      'Ubuntu',
      'Cantarell',
      'Fira Sans',
      'Droid Sans',
      '"Helvetica Neue"',
      'sans-serif',
    ].join(','),
  },
  components: {
    MuiCssBaseline: {
      styleOverrides: `
        @font-face {
          font-family: 'Quicksand-Bold';
          src: url(${QuicksandBoldWoff2});
        }
      `,
    },
  },
};

export default muiGlobalStyle;
