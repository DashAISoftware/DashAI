module.exports = {
  env: {
    browser: true,
    es2021: true,
  },
  extends: ["plugin:react/recommended", "standard-with-typescript", "prettier"],
  overrides: [],
  parserOptions: {
    ecmaVersion: "latest",
    sourceType: "module",
    tsconfigRootDir: __dirname,
    project: "tsconfig.json",
  },
  plugins: ["react"],
  rules: {
    "linebreak-style": [
      "error",
      process.platform === "win32" ? "windows" : "unix",
    ],
  },
};
