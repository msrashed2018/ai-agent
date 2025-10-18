import { useState } from 'react';
import { X, Plus } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';

interface VariableEditorProps {
  variables: Record<string, any>;
  onChange: (variables: Record<string, any>) => void;
  disabled?: boolean;
}

export function VariableEditor({ variables, onChange, disabled }: VariableEditorProps) {
  const [newKey, setNewKey] = useState('');
  const [newValue, setNewValue] = useState('');

  const entries = Object.entries(variables || {});

  const handleAdd = () => {
    if (newKey.trim() && !variables[newKey]) {
      onChange({ ...variables, [newKey]: newValue });
      setNewKey('');
      setNewValue('');
    }
  };

  const handleRemove = (key: string) => {
    const newVariables = { ...variables };
    delete newVariables[key];
    onChange(newVariables);
  };

  const handleUpdate = (key: string, value: string) => {
    onChange({ ...variables, [key]: value });
  };

  return (
    <div className="space-y-4">
      {entries.length > 0 && (
        <div className="space-y-2">
          {entries.map(([key, value]) => (
            <div key={key} className="flex items-center gap-2">
              <div className="flex-1 grid grid-cols-2 gap-2">
                <Input
                  value={key}
                  disabled
                  className="bg-gray-50 font-mono text-sm"
                />
                <Input
                  value={value}
                  onChange={(e) => handleUpdate(key, e.target.value)}
                  disabled={disabled}
                  placeholder="Value"
                  className="font-mono text-sm"
                />
              </div>
              <Button
                type="button"
                variant="ghost"
                size="sm"
                onClick={() => handleRemove(key)}
                disabled={disabled}
                className="text-red-600 hover:text-red-700 hover:bg-red-50"
              >
                <X className="h-4 w-4" />
              </Button>
            </div>
          ))}
        </div>
      )}

      <div className="border-t pt-4">
        <Label className="text-sm font-medium mb-2 block">Add Variable</Label>
        <div className="flex items-end gap-2">
          <div className="flex-1 grid grid-cols-2 gap-2">
            <div>
              <Input
                value={newKey}
                onChange={(e) => setNewKey(e.target.value)}
                placeholder="Key"
                disabled={disabled}
                className="font-mono text-sm"
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    e.preventDefault();
                    handleAdd();
                  }
                }}
              />
            </div>
            <div>
              <Input
                value={newValue}
                onChange={(e) => setNewValue(e.target.value)}
                placeholder="Default value"
                disabled={disabled}
                className="font-mono text-sm"
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    e.preventDefault();
                    handleAdd();
                  }
                }}
              />
            </div>
          </div>
          <Button
            type="button"
            onClick={handleAdd}
            disabled={!newKey.trim() || disabled || !!variables[newKey]}
            size="sm"
          >
            <Plus className="h-4 w-4 mr-1" />
            Add
          </Button>
        </div>
      </div>
    </div>
  );
}
