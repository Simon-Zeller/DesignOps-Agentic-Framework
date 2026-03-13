import React from 'react';
import { Dialog, DialogContent, DialogTitle } from '@radix-ui/react-dialog';

interface NonPrimitiveModalProps {
  title: string;
  children: React.ReactNode;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function NonPrimitiveModal({ title, children, open, onOpenChange }: NonPrimitiveModalProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogTitle>{title}</DialogTitle>
        {children}
      </DialogContent>
    </Dialog>
  );
}

export default NonPrimitiveModal;
