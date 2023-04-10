import QuicksandBoldWoff2 from "./fonts/Quicksand-Bold.woff2";

const muiGlobalStyle = {
  palette: {
    mode: "dark",
    primary: {
      light: "#008582",
      main: "#00BEBB",
      dark: "#002884",
      contrastText: "#fff",
    },
    secondary: {
      light: "#6E86E8",
      main: "#6E86E8",
      dark: "#4d5da2",
      contrastText: "#000",
    },
    background: {
      default: "#2e3037",
    },
    text: {
      primary: "#ffffff",
    },
  },
  typography: {
    fontFamily: "Quicksand-Bold",
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
