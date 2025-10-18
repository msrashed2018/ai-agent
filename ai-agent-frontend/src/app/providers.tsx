'use client';

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactNode, useEffect, useState } from 'react';
import { useAuthStore } from '@/store/auth-store';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 60 * 1000, // 1 minute
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

export function Providers({ children }: { children: ReactNode }) {
  const loadUser = useAuthStore((state) => state.loadUser);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    // Only load user data on client side after hydration
    if (typeof window !== 'undefined') {
      loadUser();
    }
    setMounted(true);
  }, [loadUser]);

  // Prevent hydration mismatch by not rendering until mounted
  if (!mounted) {
    return null;
  }

  return (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );
}
