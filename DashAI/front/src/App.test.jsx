import React from 'react';
// import { render, screen } from '@testing-library/react';
import { render } from '@testing-library/react';
import { BrowserRouter as Router } from 'react-router-dom';
import { createTheme, ThemeProvider } from '@mui/material/styles';
import '@testing-library/jest-dom';
import App from './App';
import theme from './styles/theme';

const myTheme = createTheme(theme);

test('loads and displays model', async () => {
  render(
    <Router>
      <ThemeProvider theme={myTheme}>
        <App />
      </ThemeProvider>
    </Router>
  );
  // expect(screen.getByText('Learn React')).toBeInTheDocument();
});
