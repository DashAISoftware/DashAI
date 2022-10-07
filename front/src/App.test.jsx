import React from 'react';
// import { render, screen } from '@testing-library/react';
import { render } from '@testing-library/react';
import { BrowserRouter as Router } from 'react-router-dom';
import '@testing-library/jest-dom';
import App from './App';

test('loads and displays model', async () => {
  render(
    <Router>
      <App />
    </Router>
  );
  // expect(screen.getByText('Learn React')).toBeInTheDocument();
});
