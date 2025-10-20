import { useMutation } from '@tanstack/react-query';
import { apiClient } from '@/lib/api-client';
import { toast } from 'sonner';

/**
 * Hook for logging out the current user session
 * Invalidates the current session on the server and clears local auth state
 */
export function useLogout() {
  return useMutation({
    mutationFn: () => apiClient.logout(),
    onSuccess: () => {
      toast.success('Logged out successfully');
    },
    onError: (error: any) => {
      const message = error.response?.data?.detail || 'Logout failed';
      toast.error(message);
      // Still clear local auth even if server logout fails
      apiClient.logout();
    },
  });
}

/**
 * Hook for logging out all user sessions
 * Invalidates all sessions for the user on the server and clears local auth state
 */
export function useLogoutAll() {
  return useMutation({
    mutationFn: () => apiClient.logoutAll(),
    onSuccess: () => {
      toast.success('Logged out from all sessions successfully');
    },
    onError: (error: any) => {
      const message = error.response?.data?.detail || 'Logout from all sessions failed';
      toast.error(message);
      // Still clear local auth even if server logout fails
      apiClient.logout();
    },
  });
}
