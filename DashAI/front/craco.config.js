module.exports = {
  webpack: {
    alias: {
      '@mui/styled-engine': '@mui/styled-engine-sc',
    },
  },
  jest: {
    configure: (jestConfig) => {
        jestConfig.moduleNameMapper = { "@mui/styled-engine": "@mui/styled-engine-sc" };
        return jestConfig;
    },
  },
};