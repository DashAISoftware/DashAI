const react = require("eslint-plugin-react");

module.exports = {
  languageOptions: {
    ecmaVersion: 2021,
    sourceType: "module",
    globals: {
      window: "readonly",
      document: "readonly",
    },
    parserOptions: {
      tsconfigRootDir: __dirname,
      project: "tsconfig.json",
      ecmaFeatures: {
        jsx: true,
      },
    },
  },
  files: ["**/*.{js,jsx}"],
  plugins: {
    react,
  },

  settings: {
    react: {
      version: "detect",
    },
  },
};
