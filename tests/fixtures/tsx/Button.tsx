import React from 'react';
import { Pressable, Text } from '../primitives';

interface ButtonProps {
  label: string;
  disabled?: boolean;
  onPress: () => void;
  variant?: 'primary' | 'secondary';
}

export function Button({ label, disabled = false, onPress, variant = 'primary' }: ButtonProps) {
  return (
    <Pressable
      onPress={onPress}
      disabled={disabled}
      aria-disabled={disabled}
      style={{
        backgroundColor: disabled
          ? 'var(--color-interactive-disabled)'
          : 'var(--color-interactive-default)',
        borderRadius: 'var(--radius-md)',
        paddingLeft: 'var(--space-4)',
        paddingRight: 'var(--space-4)',
        paddingTop: 'var(--space-2)',
        paddingBottom: 'var(--space-2)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
      }}
    >
      <Text
        style={{
          color: 'var(--color-interactive-foreground)',
          fontSize: 'var(--typography-body-size)',
        }}
      >
        {label}
      </Text>
    </Pressable>
  );
}

export default Button;
