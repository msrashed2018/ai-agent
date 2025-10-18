'use client';

import { ProtectedRoute } from '@/components/auth/protected-route';
import { AppLayout } from '@/components/layout/app-layout';

export default function AdminLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <ProtectedRoute>
      <AppLayout>{children}</AppLayout>
    </ProtectedRoute>
  );
}
