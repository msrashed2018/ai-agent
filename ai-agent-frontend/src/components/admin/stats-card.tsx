import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { LucideIcon } from 'lucide-react';

interface StatsCardProps {
  title: string;
  value: string | number;
  icon: LucideIcon;
  loading?: boolean;
  subtitle?: string;
  description?: string;
  trend?: {
    value: number;
    isPositive: boolean;
  };
}

export function StatsCard({
  title,
  value,
  icon: Icon,
  loading,
  subtitle,
  description,
  trend
}: StatsCardProps) {
  return (
    <Card className="hover:shadow-lg transition-shadow">
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <div className="space-y-1">
          <CardTitle className="text-sm font-medium text-gray-600">{title}</CardTitle>
          {description && (
            <p className="text-xs text-gray-500">{description}</p>
          )}
        </div>
        <div className="h-12 w-12 rounded-full bg-primary/10 flex items-center justify-center">
          <Icon className="h-6 w-6 text-primary" />
        </div>
      </CardHeader>
      <CardContent>
        {loading ? (
          <div className="space-y-2">
            <Skeleton className="h-10 w-32" />
            {subtitle && <Skeleton className="h-4 w-40" />}
          </div>
        ) : (
          <>
            <div className="text-3xl font-bold">{value}</div>
            {subtitle && <p className="text-xs text-gray-600 mt-2">{subtitle}</p>}
            {trend && (
              <p className={`text-xs mt-2 font-medium ${trend.isPositive ? 'text-green-600' : 'text-red-600'}`}>
                {trend.isPositive ? '↑' : '↓'} {Math.abs(trend.value)}% from last period
              </p>
            )}
          </>
        )}
      </CardContent>
    </Card>
  );
}
