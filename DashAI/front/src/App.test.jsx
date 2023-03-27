import React from 'react';
// import { render, screen } from '@testing-library/react';
import { render } from '@testing-library/react';
import { BrowserRouter as Router } from 'react-router-dom';
import { createTheme, ThemeProvider } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import '@testing-library/jest-dom';
import App from './App';
import theme from './styles/theme';
import muiGlobalStyle from './styles/muiGlobalStyles';


const myTheme = createTheme({ ...theme, ...muiGlobalStyle });

test('loads and displays model', async () => {
  render(
    <Router>
      <ThemeProvider theme={myTheme}>
        <CssBaseline />
        <App />
      </ThemeProvider>
    </Router>
  );
  // expect(screen.getByText('Learn React')).toBeInTheDocument();
});
