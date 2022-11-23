import React from 'react';
// import { render, screen } from '@testing-library/react';
import { render } from '@testing-library/react';
import { BrowserRouter as Router } from 'react-router-dom';
import { ThemeProvider } from 'styled-components';
import '@testing-library/jest-dom';
import App from './App';
import theme from './styles/theme';

test('loads and displays model', async () => {
  render(
    <Router>
      <ThemeProvider theme={theme}>
        <App />
      </ThemeProvider>
    </Router>
  );
  // expect(screen.getByText('Learn React')).toBeInTheDocument();
});
