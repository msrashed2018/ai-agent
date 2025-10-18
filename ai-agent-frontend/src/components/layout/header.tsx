'use client';

import { Menu } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { UserMenu } from './user-menu';

interface HeaderProps {
  onMenuClick: () => void;
  title?: string;
}

export function Header({ onMenuClick, title }: HeaderProps) {
  return (
    <header className="sticky top-0 z-40 flex h-16 items-center gap-4 border-b bg-background px-6">
      {/* Mobile menu button */}
      <Button
        variant="ghost"
        size="icon"
        className="lg:hidden"
        onClick={onMenuClick}
      >
        <Menu className="h-5 w-5" />
        <span className="sr-only">Toggle menu</span>
      </Button>

      {/* Page title (optional) */}
      {title && (
        <div className="flex-1">
          <h1 className="text-xl font-semibold">{title}</h1>
        </div>
      )}

      {/* Spacer */}
      {!title && <div className="flex-1" />}

      {/* User menu */}
      <UserMenu />
    </header>
  );
}
