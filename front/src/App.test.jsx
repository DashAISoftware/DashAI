import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import App from './App';

test('loads and displays model', async () => {
  render(<App />);
  expect(screen.getByText('Learn React')).toBeInTheDocument();
});
