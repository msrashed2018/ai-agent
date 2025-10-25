'use client';

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { ToolGroupResponse } from '@/types/api';

interface ToolGroupSelectorProps {
  toolGroups: ToolGroupResponse[];
  value?: string;
  onChange: (value: string | undefined) => void;
  placeholder?: string;
  disabled?: boolean;
  isLoading?: boolean;
}

export function ToolGroupSelector({
  toolGroups,
  value,
  onChange,
  placeholder = 'Select a tool group',
  disabled = false,
  isLoading = false,
}: ToolGroupSelectorProps) {
  return (
    <div className="space-y-2">
      <label className="block text-sm font-medium text-gray-700">
        Tool Group
      </label>
      <Select
        value={value || '__none__'}
        onValueChange={(v) => onChange(v === '__none__' ? undefined : v)}
        disabled={disabled || isLoading}
      >
        <SelectTrigger>
          <SelectValue placeholder={placeholder} />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="__none__">None</SelectItem>
          {toolGroups.map((group) => (
            <SelectItem key={group.id} value={group.id}>
              <div className="flex items-center gap-2">
                <span>{group.name}</span>
                {group.description && (
                  <span className="text-xs text-gray-500">
                    ({group.description})
                  </span>
                )}
              </div>
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
      <p className="text-sm text-gray-500">
        Selecting a tool group will automatically apply its allowed and disallowed tools to this task.
      </p>
    </div>
  );
}
