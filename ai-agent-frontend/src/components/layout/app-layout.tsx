'use client';

import { useState } from 'react';
import { Sidebar } from './sidebar';
import { Header } from './header';

interface AppLayoutProps {
  children: React.ReactNode;
  title?: string;
}

export function AppLayout({ children, title }: AppLayoutProps) {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <div className="flex h-screen overflow-hidden">
      {/* Sidebar */}
      <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />

      {/* Main content area */}
      <div className="flex flex-1 flex-col overflow-hidden lg:ml-0">
        {/* Header */}
        <Header onMenuClick={() => setSidebarOpen(true)} title={title} />

        {/* Page content */}
        <main className="flex-1 overflow-y-auto bg-muted/10 p-6">
          {children}
        </main>
      </div>
    </div>
  );
}
