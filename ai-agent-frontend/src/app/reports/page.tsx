'use client';

import { useState } from 'react';
import { useReports } from '@/hooks/use-reports';
import { useSessions } from '@/hooks/use-sessions';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { ReportTable } from '@/components/reports/report-table';
import { Search, Filter, FileText } from 'lucide-react';

export default function ReportsPage() {
  const [searchQuery, setSearchQuery] = useState('');
  const [filterType, setFilterType] = useState<string>('all');
  const [filterFormat, setFilterFormat] = useState<string>('all');
  const [filterSession, setFilterSession] = useState<string>('all');

  // Build query params
  const queryParams = {
    report_type: filterType === 'all' ? undefined : filterType,
    session_id: filterSession === 'all' ? undefined : filterSession,
  };

  const { data: reportsData, isLoading } = useReports(queryParams);
  const { data: sessionsData } = useSessions({ page_size: 100 });

  // Client-side filtering for search and format
  const filteredReports = reportsData?.items?.filter((report) => {
    // Search filter
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      const matchesTitle = report.title.toLowerCase().includes(query);
      const matchesDescription = report.description?.toLowerCase().includes(query);
      const matchesTags = report.tags?.some((tag) => tag.toLowerCase().includes(query));
      if (!matchesTitle && !matchesDescription && !matchesTags) {
        return false;
      }
    }

    // Format filter
    if (filterFormat !== 'all' && report.file_format !== filterFormat) {
      return false;
    }

    return true;
  });

  return (
    <div className="container mx-auto py-8 px-4">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <FileText className="h-8 w-8" />
            Reports
          </h1>
          <p className="text-gray-600 mt-1">View and download generated reports</p>
        </div>
      </div>

      <Card className="mb-6">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Filter className="h-5 w-5" />
            Filters
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">Search</label>
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                <Input
                  placeholder="Search reports..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-9"
                />
              </div>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Type</label>
              <Select value={filterType} onValueChange={setFilterType}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Types</SelectItem>
                  <SelectItem value="task_execution">Task Execution</SelectItem>
                  <SelectItem value="manual">Manual</SelectItem>
                  <SelectItem value="scheduled">Scheduled</SelectItem>
                  <SelectItem value="auto_generated">Auto Generated</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Format</label>
              <Select value={filterFormat} onValueChange={setFilterFormat}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Formats</SelectItem>
                  <SelectItem value="html">HTML</SelectItem>
                  <SelectItem value="pdf">PDF</SelectItem>
                  <SelectItem value="json">JSON</SelectItem>
                  <SelectItem value="markdown">Markdown</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Session</label>
              <Select value={filterSession} onValueChange={setFilterSession}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Sessions</SelectItem>
                  {sessionsData?.items?.map((session) => (
                    <SelectItem key={session.id} value={session.id}>
                      {session.name || `Session ${session.id.slice(0, 8)}...`}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>
            {filteredReports ? `${filteredReports.length} Reports` : 'Loading...'}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <ReportTable reports={filteredReports} loading={isLoading} />
        </CardContent>
      </Card>
    </div>
  );
}
