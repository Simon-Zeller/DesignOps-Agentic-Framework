import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { Button } from './Button';

describe('Button', () => {
  it('renders the label', () => {
    render(<Button label="Click me" onPress={() => {}} />);
    expect(screen.getByText('Click me')).toBeDefined();
  });

  it('applies disabled state', () => {
    render(<Button label="Submit" disabled onPress={() => {}} />);
    const btn = screen.getByRole('button');
    expect(btn.getAttribute('aria-disabled')).toBe('true');
  });
});

// @accessibility-placeholder
