import { MCPServerType } from '@/types/api';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Server, Zap, Globe } from 'lucide-react';
import { cn } from '@/lib/utils';

interface TypeSelectorProps {
  selectedType: MCPServerType | null;
  onSelect: (type: MCPServerType) => void;
}

const SERVER_TYPES = [
  {
    type: 'stdio' as MCPServerType,
    label: 'STDIO',
    description: 'Standard input/output process',
    icon: Server,
    color: 'text-blue-600',
    bgColor: 'bg-blue-50',
    borderColor: 'border-blue-200',
  },
  {
    type: 'sse' as MCPServerType,
    label: 'SSE',
    description: 'Server-sent events',
    icon: Zap,
    color: 'text-purple-600',
    bgColor: 'bg-purple-50',
    borderColor: 'border-purple-200',
  },
  {
    type: 'http' as MCPServerType,
    label: 'HTTP',
    description: 'HTTP REST API',
    icon: Globe,
    color: 'text-green-600',
    bgColor: 'bg-green-50',
    borderColor: 'border-green-200',
  },
];

export function TypeSelector({ selectedType, onSelect }: TypeSelectorProps) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      {SERVER_TYPES.map(({ type, label, description, icon: Icon, color, bgColor, borderColor }) => (
        <Card
          key={type}
          className={cn(
            'cursor-pointer transition-all hover:shadow-md',
            selectedType === type && `ring-2 ring-offset-2 ring-primary ${borderColor}`
          )}
          onClick={() => onSelect(type)}
        >
          <CardHeader className="pb-3">
            <div className={cn('w-12 h-12 rounded-lg flex items-center justify-center mb-2', bgColor)}>
              <Icon className={cn('h-6 w-6', color)} />
            </div>
            <CardTitle className="text-lg">{label}</CardTitle>
            <CardDescription className="text-sm">{description}</CardDescription>
          </CardHeader>
        </Card>
      ))}
    </div>
  );
}

export function getTypeColor(type: MCPServerType): string {
  const typeInfo = SERVER_TYPES.find((t) => t.type === type);
  return typeInfo?.color || 'text-gray-600';
}

export function getTypeBgColor(type: MCPServerType): string {
  const typeInfo = SERVER_TYPES.find((t) => t.type === type);
  return typeInfo?.bgColor || 'bg-gray-50';
}
