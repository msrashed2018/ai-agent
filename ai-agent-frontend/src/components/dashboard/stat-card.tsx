import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { LucideIcon } from 'lucide-react';

interface StatCardProps {
  title: string;
  value: string | number;
  icon: LucideIcon;
  loading?: boolean;
  subtitle?: string;
  trend?: {
    value: number;
    isPositive: boolean;
  };
}

export function StatCard({ title, value, icon: Icon, loading, subtitle, trend }: StatCardProps) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium text-gray-600">{title}</CardTitle>
        <Icon className="h-4 w-4 text-gray-600" />
      </CardHeader>
      <CardContent>
        {loading ? (
          <div className="space-y-2">
            <Skeleton className="h-8 w-24" />
            {subtitle && <Skeleton className="h-4 w-32" />}
          </div>
        ) : (
          <>
            <div className="text-2xl font-bold">{value}</div>
            {subtitle && <p className="text-xs text-gray-600 mt-1">{subtitle}</p>}
            {trend && (
              <p className={`text-xs mt-1 ${trend.isPositive ? 'text-green-600' : 'text-red-600'}`}>
                {trend.isPositive ? '+' : ''}{trend.value}% from last month
              </p>
            )}
          </>
        )}
      </CardContent>
    </Card>
  );
}
