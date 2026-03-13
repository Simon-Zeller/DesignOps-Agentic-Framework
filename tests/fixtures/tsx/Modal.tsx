import React from 'react';
import { Box, Pressable, Text } from '../primitives';

interface ModalProps {
  title: string;
  children: React.ReactNode;
  isOpen: boolean;
  onClose: () => void;
}

export function Modal({ title, children, isOpen, onClose }: ModalProps) {
  if (!isOpen) return null;

  return (
    <Box
      style={{
        position: 'fixed',
        inset: 0,
        backgroundColor: 'rgba(0,0,0,0.5)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
      }}
    >
      <Box
        style={{
          backgroundColor: 'var(--color-surface-default)',
          borderRadius: 'var(--radius-lg)',
          padding: 'var(--space-6)',
          minWidth: '320px',
        }}
      >
        <Text style={{ fontSize: 'var(--typography-heading-size)' }}>{title}</Text>
        {children}
        <Pressable onPress={onClose}>
          <Text>Close</Text>
        </Pressable>
      </Box>
    </Box>
  );
}

export default Modal;
