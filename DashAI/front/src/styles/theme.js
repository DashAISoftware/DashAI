const getTheme = (mode) => ({
  spacing: 4,

  layout: {
    spacing: {
      xs: 1, //  4px — icon gaps, chip padding, tight inline elements
      sm: 2, //  8px — between items in the same group, form field rows
      md: 3, // 12px — compact section spacing, between related controls
      lg: 4, // 16px — card padding, internal section spacing
      xl: 6, // 24px — between distinct sections within a page
      xxl: 8, // 32px — between major content blocks, dialog padding
      xxxl: 12, // 48px — wide page-level spacing
      max: 16, // 64px — hero / full-page sections
    },
    dimensions: {
      appBarHeight: "53px",
      appBarHeightLg: "74px",
      sidebarWidth: "220px",
    },
  },

  palette: {
    mode,

    primary: {
      light: "#A7C7FF",
      main: "#2C7AFF",
      dark: "#001C34",
      contrastText: "#FEFEFF",
    },

    secondary: {
      light: "#5B96D6",
      main: "#1A5FA3",
      dark: "#001C34",
      contrastText: "#FEFEFF",
    },

    divider: mode === "dark" ? "rgba(254,254,255,0.10)" : "rgba(0,28,52,0.10)",

    background:
      mode === "dark"
        ? {
            default: "#191817",
            paper: "#1F1E1D",
            box: "#1B1A19",
          }
        : {
            default: "#FEFEFF",
            paper: "#FFFFFF",
            box: "#F5F8FF",
          },

    text:
      mode === "dark"
        ? {
            primary: "#fefeff",
            secondary: "rgba(254,254,255,0.70)",
            disabled: "rgba(254,254,255,0.40)",
          }
        : {
            primary: "#191817",
            secondary: "rgba(25,24,23,0.60)",
            disabled: "rgba(25,24,23,0.35)",
          },

    action:
      mode === "dark"
        ? {
            hover: "rgba(44,122,255,0.06)",
            selected: "rgba(44,122,255,0.10)",
            disabled: "rgba(254,254,255,0.30)",
            disabledBackground: "rgba(254,254,255,0.12)",
          }
        : {
            hover: "rgba(44,122,255,0.06)",
            selected: "rgba(44,122,255,0.10)",
            disabled: "rgba(0,0,0,0.26)",
            disabledBackground: "rgba(0,0,0,0.12)",
          },

    error: {
      main: mode === "dark" ? "#ff8383" : "#d32f2f",
    },
    warning: {
      main: mode === "dark" ? "#fbc02d" : "#f9a825",
    },
    success: {
      main: "#43A047",
      light: "#4caf50",
    },
    info: {
      main: "#2C7AFF",
      light: "#A7C7FF",
    },

    // Placeholder highlight for prompt templates (chunks, input, etc.)
    placeholder:
      mode === "dark"
        ? {
            bg: "rgba(255, 183, 77, 0.15)",
            text: "#FFB74D",
            border: "rgba(255, 183, 77, 0.30)",
          }
        : {
            bg: "rgba(249, 168, 37, 0.12)",
            text: "#E65100",
            border: "rgba(230, 81, 0, 0.25)",
          },

    // Module accent colors — dark uses lighter variants, light uses darker variants
    accent: {
      // Datasets → orange-brown
      amber: mode === "dark" ? "#FFA578" : "#79310C",
      amberDim:
        mode === "dark" ? "rgba(255,165,120,0.12)" : "rgba(121,49,12,0.12)",
      amberBorder:
        mode === "dark" ? "rgba(255,165,120,0.22)" : "rgba(121,49,12,0.22)",
      amberGlow:
        mode === "dark" ? "rgba(255,165,120,0.04)" : "rgba(121,49,12,0.04)",
      // Models → blue
      teal: mode === "dark" ? "#A7C7FF" : "#2C7AFF",
      tealDim:
        mode === "dark" ? "rgba(167,199,255,0.12)" : "rgba(44,122,255,0.12)",
      tealBorder:
        mode === "dark" ? "rgba(167,199,255,0.22)" : "rgba(44,122,255,0.22)",
      tealGlow:
        mode === "dark" ? "rgba(167,199,255,0.04)" : "rgba(44,122,255,0.04)",
      // Generative → teal/mint
      purple: mode === "dark" ? "#90F1C4" : "#005967",
      purpleDim:
        mode === "dark" ? "rgba(144,241,196,0.12)" : "rgba(0,89,103,0.12)",
      purpleBorder:
        mode === "dark" ? "rgba(144,241,196,0.22)" : "rgba(0,89,103,0.22)",
      purpleGlow:
        mode === "dark" ? "rgba(144,241,196,0.04)" : "rgba(0,89,103,0.04)",
      // Plugins → purple
      coral: mode === "dark" ? "#FEE8FF" : "#A54DA9",
      coralDim:
        mode === "dark" ? "rgba(254,232,255,0.12)" : "rgba(165,77,169,0.12)",
      coralBorder:
        mode === "dark" ? "rgba(254,232,255,0.22)" : "rgba(165,77,169,0.22)",
      coralGlow:
        mode === "dark" ? "rgba(254,232,255,0.04)" : "rgba(165,77,169,0.04)",
    },

    status: {
      notStarted: mode === "dark" ? "#626262" : "#9e9e9e",
      started: "#2C7AFF",
      finished: "#43A047",
      delivered: "#2C7AFF",
      error: mode === "dark" ? "#A70909" : "#c62828",
    },

    dataType: {
      numerical: "#00BEBB",
      integer: "#5c6bc0",
      categorical: "#9c27b0",
      text: "#d4a054",
      boolean: "#8bc34a",
      datetime: "#e91e63",
      image: "#6E86E8",
      default: "#757575",
    },

    chart: {
      train: "#66bb6a",
      test: "#42a5f5",
      validation: "#ff9800",
      palette: [
        "#66bb6a",
        "#42a5f5",
        "#ff9800",
        "#ab47bc",
        "#ef5350",
        "#26a69a",
        "#8d6e63",
        "#78909c",
      ],
    },

    ui:
      mode === "dark"
        ? {
            border: "rgba(254,254,255,0.10)",
            borderLight: "rgba(254,254,255,0.06)",
            borderMed: "rgba(254,254,255,0.16)",
            borderDark: "rgba(254,254,255,0.22)",
            panelDark: "#1B1A19",
            panelMedium: "#1F1E1D",
            panelLight: "#232221",
            scrollbar: "rgba(254,254,255,0.20)",
            scrollbarHover: "rgba(254,254,255,0.35)",
            hover: "rgba(254,254,255,0.04)",
            divider: "rgba(254,254,255,0.10)",
            box: "#1B1A19",
            disabled: "#232221",
            rowDisabled: "rgba(255,255,255,0.04)",
          }
        : {
            border: "rgba(0,28,52,0.10)",
            borderLight: "rgba(0,28,52,0.06)",
            borderMed: "rgba(0,28,52,0.16)",
            borderDark: "rgba(0,28,52,0.22)",
            panelDark: "#EEF2FF",
            panelMedium: "#F5F8FF",
            panelLight: "#FFFFFF",
            scrollbar: "#A7C7FF",
            scrollbarHover: "#7AABFF",
            hover: "rgba(44,122,255,0.04)",
            divider: "rgba(0,28,52,0.10)",
            box: "#F5F8FF",
            disabled: "#EEF2FF",
            rowDisabled: "rgba(44,122,255,0.04)",
          },
  },

  typography: {
    fontFamily: '"Geist", sans-serif',

    h1: { fontSize: "28px", fontWeight: 700, letterSpacing: "-0.01em" },
    h2: { fontSize: "22px", fontWeight: 600, letterSpacing: "-0.01em" },
    h3: { fontSize: "20px", fontWeight: 600, letterSpacing: "-0.01em" },
    h4: { fontSize: "20px", fontWeight: 600, letterSpacing: "-0.01em" },
    h5: { fontSize: "16px", fontWeight: 600 },
    h6: { fontSize: "16px", fontWeight: 600 },

    subtitle1: { fontSize: "17px", fontWeight: 400 },
    subtitle2: { fontSize: "16px", fontWeight: 400 },
    body1: { fontSize: "16px", fontWeight: 400, lineHeight: 1.6 },
    body2: { fontSize: "12px", fontWeight: 400, lineHeight: 1.5 },
    caption: { fontSize: "12px", fontWeight: 400 },
    code: {
      fontFamily: '"Geist Mono", monospace',
      fontSize: "12px",
      fontWeight: 400,
    },

    navItem: { fontSize: "12px", fontWeight: 400 },
    tabLabel: {
      fontFamily: '"Geist Mono", monospace',
      fontSize: "10px",
      letterSpacing: "0.12em",
      textTransform: "uppercase",
    },
    sectionLabel: {
      fontFamily: '"Geist Mono", monospace',
      fontSize: "9px",
      letterSpacing: "0.2em",
      textTransform: "uppercase",
    },
    statusBadge: {
      fontFamily: '"Geist Mono", monospace',
      fontSize: "8.5px",
      letterSpacing: "0.12em",
      textTransform: "uppercase",
    },
    button: {
      fontSize: "16px",
      fontWeight: 500,
      letterSpacing: "-0.01em",
      textTransform: "uppercase",
    },
  },

  components: {
    MuiIconButton: {
      styleOverrides: {
        colorPrimary: ({ theme }) => ({
          "&:hover": {
            backgroundColor: `${theme.palette.secondary.main}1A`,
          },
        }),
      },
    },
    MuiButton: {
      styleOverrides: {
        containedPrimary: ({ theme }) => ({
          "&:hover": {
            backgroundColor: theme.palette.secondary.main,
          },
        }),
      },
    },
    MuiAlert: {
      styleOverrides: {
        standardWarning: ({ theme }) =>
          theme.palette.mode === "light"
            ? {
                backgroundColor: `${theme.palette.warning.main}35`,
                border: `1px solid ${theme.palette.warning.main}70`,
              }
            : {},
      },
    },
    MuiCssBaseline: {
      styleOverrides: `
        ::-webkit-scrollbar { width: 12px; }
        ::-webkit-scrollbar-track {
          -webkit-box-shadow: inset 0 0 6px rgba(0,0,0,0.3);
          -webkit-border-radius: 10px;
          border-radius: 10px;
        }
        ::-webkit-scrollbar-thumb {
          -webkit-border-radius: 10px;
          border-radius: 10px;
          background: ${
            mode === "dark" ? "rgba(254,254,255,0.20)" : "rgba(0,28,52,0.25)"
          };
          -webkit-box-shadow: inset 0 0 6px rgba(0,0,0,0.2);
        }
        ::-webkit-scrollbar-thumb:window-inactive {
          background: ${
            mode === "dark" ? "rgba(44,122,255,0.12)" : "rgba(0,28,52,0.15)"
          };
        }
      `,
    },
  },
});

export default getTheme;
