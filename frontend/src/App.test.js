import { render, screen } from '@testing-library/react';
import App from './App';

test('renders MediBot welcome message', () => {
  render(<App />);
  expect(screen.getByRole('heading', { name: /MediBot/i })).toBeInTheDocument();
  expect(screen.getByText(/AI Medical Assistant/i)).toBeInTheDocument();
});
