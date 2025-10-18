import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Plus, Trash2 } from 'lucide-react';

interface KeyValuePair {
  key: string;
  value: string;
}

interface KeyValueEditorProps {
  label: string;
  value: Record<string, string>;
  onChange: (value: Record<string, string>) => void;
  placeholder?: {
    key: string;
    value: string;
  };
}

export function KeyValueEditor({
  label,
  value,
  onChange,
  placeholder = { key: 'Key', value: 'Value' },
}: KeyValueEditorProps) {
  const pairs: KeyValuePair[] = Object.entries(value).map(([key, val]) => ({
    key,
    value: val,
  }));

  const handleAdd = () => {
    const newPairs = [...pairs, { key: '', value: '' }];
    updatePairs(newPairs);
  };

  const handleRemove = (index: number) => {
    const newPairs = pairs.filter((_, i) => i !== index);
    updatePairs(newPairs);
  };

  const handleKeyChange = (index: number, newKey: string) => {
    const newPairs = [...pairs];
    newPairs[index].key = newKey;
    updatePairs(newPairs);
  };

  const handleValueChange = (index: number, newValue: string) => {
    const newPairs = [...pairs];
    newPairs[index].value = newValue;
    updatePairs(newPairs);
  };

  const updatePairs = (newPairs: KeyValuePair[]) => {
    const obj: Record<string, string> = {};
    newPairs.forEach((pair) => {
      if (pair.key.trim()) {
        obj[pair.key.trim()] = pair.value;
      }
    });
    onChange(obj);
  };

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <Label>{label}</Label>
        <Button type="button" variant="outline" size="sm" onClick={handleAdd}>
          <Plus className="h-4 w-4 mr-1" />
          Add
        </Button>
      </div>

      <div className="space-y-2">
        {pairs.length === 0 ? (
          <div className="text-sm text-gray-500 text-center py-4 border-2 border-dashed rounded-lg">
            No {label.toLowerCase()} defined. Click "Add" to create one.
          </div>
        ) : (
          pairs.map((pair, index) => (
            <div key={index} className="flex gap-2">
              <Input
                placeholder={placeholder.key}
                value={pair.key}
                onChange={(e) => handleKeyChange(index, e.target.value)}
                className="flex-1"
              />
              <Input
                placeholder={placeholder.value}
                value={pair.value}
                onChange={(e) => handleValueChange(index, e.target.value)}
                className="flex-1"
              />
              <Button
                type="button"
                variant="outline"
                size="icon"
                onClick={() => handleRemove(index)}
              >
                <Trash2 className="h-4 w-4" />
              </Button>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
