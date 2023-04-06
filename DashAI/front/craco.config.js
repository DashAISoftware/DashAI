module.exports = {
  webpack: {
    alias: {
      "@mui/styled-engine": "@mui/styled-engine-sc",
    },
    typescript: {
      enableTypeChecking: true /* (default value) */,
    },
  },
  jest: {
    configure: (jestConfig) => {
      jestConfig.moduleNameMapper = {
        "@mui/styled-engine": "@mui/styled-engine-sc",
      };
      return jestConfig;
    },
  },
};
