import QuicksandBoldWoff2 from "./fonts/Quicksand-Bold.woff2";

const theme = {
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
      paper: "#121212",
    },
    text: {
      primary: "#ffffff",
    },
    error: {
      main: "#ff8383",
    },
    warning: {
      main: "#f1ae61",
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
        /* custom scrollbar */

        ::-webkit-scrollbar {
          width: 12px;
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
      `,
    },
  },
};

export default theme;
