import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/lib/api-client';
import type {
  ReportResponse,
  ReportListResponse,
  PaginationParams,
} from '@/types/api';
import { toast } from 'sonner';

// Query Keys
const REPORTS_QUERY_KEY = 'reports';
const REPORT_QUERY_KEY = 'report';

interface UseReportsParams extends PaginationParams {
  session_id?: string;
  report_type?: string;
}

// ============================================================================
// Reports Queries
// ============================================================================

export function useReports(params?: UseReportsParams) {
  return useQuery({
    queryKey: [REPORTS_QUERY_KEY, params],
    queryFn: () => apiClient.listReports(params),
  });
}

export function useReport(reportId: string | undefined) {
  return useQuery({
    queryKey: [REPORT_QUERY_KEY, reportId],
    queryFn: () => apiClient.getReport(reportId!),
    enabled: !!reportId,
  });
}

// ============================================================================
// Download Mutation
// ============================================================================

export function useDownloadReport() {
  return useMutation({
    mutationFn: async ({ reportId, format, fileName }: { reportId: string; format: string; fileName: string }) => {
      const blob = await apiClient.downloadReport(reportId, format);

      // Create download link
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = fileName;
      document.body.appendChild(link);
      link.click();

      // Cleanup
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);

      return { success: true };
    },
    onSuccess: () => {
      toast.success('Report downloaded successfully');
    },
    onError: (error: any) => {
      const message = error.response?.data?.detail || 'Failed to download report';
      toast.error(message);
    },
  });
}
