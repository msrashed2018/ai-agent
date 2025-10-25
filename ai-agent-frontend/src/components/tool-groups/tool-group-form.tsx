'use client';

import { useState } from 'react';
import { ToolGroupCreateRequest, ToolGroupResponse } from '@/types/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { X } from 'lucide-react';

interface ToolGroupFormProps {
  initialData?: ToolGroupResponse | null;
  isSubmitting: boolean;
  onSubmit: (data: ToolGroupCreateRequest) => void;
  onCancel: () => void;
}

export function ToolGroupForm({
  initialData,
  isSubmitting,
  onSubmit,
  onCancel,
}: ToolGroupFormProps) {
  const [name, setName] = useState(initialData?.name || '');
  const [description, setDescription] = useState(initialData?.description || '');
  const [allowedToolsInput, setAllowedToolsInput] = useState('');
  const [allowedTools, setAllowedTools] = useState<string[]>(initialData?.allowed_tools || []);
  const [disallowedToolsInput, setDisallowedToolsInput] = useState('');
  const [disallowedTools, setDisallowedTools] = useState<string[]>(initialData?.disallowed_tools || []);

  const handleAddAllowedTool = () => {
    const tool = allowedToolsInput.trim();
    if (tool && !allowedTools.includes(tool)) {
      setAllowedTools([...allowedTools, tool]);
      setAllowedToolsInput('');
    }
  };

  const handleRemoveAllowedTool = (tool: string) => {
    setAllowedTools(allowedTools.filter((t) => t !== tool));
  };

  const handleAddDisallowedTool = () => {
    const tool = disallowedToolsInput.trim();
    if (tool && !disallowedTools.includes(tool)) {
      setDisallowedTools([...disallowedTools, tool]);
      setDisallowedToolsInput('');
    }
  };

  const handleRemoveDisallowedTool = (tool: string) => {
    setDisallowedTools(disallowedTools.filter((t) => t !== tool));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    if (!name.trim()) {
      alert('Tool group name is required');
      return;
    }

    onSubmit({
      name: name.trim(),
      description: description.trim() || undefined,
      allowed_tools: allowedTools,
      disallowed_tools: disallowedTools,
    });
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* Basic Info */}
      <div className="space-y-4">
        <h3 className="text-lg font-semibold">Basic Information</h3>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Tool Group Name <span className="text-red-500">*</span>
          </label>
          <Input
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="e.g., k8s-read-only, aws-safe-tools"
            disabled={isSubmitting}
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Description
          </label>
          <Textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Describe the purpose of this tool group..."
            rows={3}
            disabled={isSubmitting}
          />
        </div>
      </div>

      {/* Allowed Tools */}
      <div className="space-y-4">
        <h3 className="text-lg font-semibold">Allowed Tools</h3>
        <p className="text-sm text-gray-600">Tools that can be executed. Examples: Bash(*), Bash(kubectl get:*)</p>

        <div className="flex gap-2">
          <Input
            value={allowedToolsInput}
            onChange={(e) => setAllowedToolsInput(e.target.value)}
            placeholder="Enter tool pattern and press Add"
            disabled={isSubmitting}
            onKeyPress={(e) => {
              if (e.key === 'Enter') {
                e.preventDefault();
                handleAddAllowedTool();
              }
            }}
          />
          <Button
            type="button"
            onClick={handleAddAllowedTool}
            disabled={isSubmitting || !allowedToolsInput.trim()}
            variant="outline"
          >
            Add
          </Button>
        </div>

        {allowedTools.length > 0 && (
          <div className="flex flex-wrap gap-2">
            {allowedTools.map((tool) => (
              <div
                key={tool}
                className="inline-flex items-center gap-2 rounded-full bg-blue-100 px-3 py-1 text-sm text-blue-900"
              >
                {tool}
                <button
                  type="button"
                  onClick={() => handleRemoveAllowedTool(tool)}
                  className="hover:text-blue-700"
                  disabled={isSubmitting}
                >
                  <X className="h-4 w-4" />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Disallowed Tools */}
      <div className="space-y-4">
        <h3 className="text-lg font-semibold">Disallowed Tools</h3>
        <p className="text-sm text-gray-600">Tools that cannot be executed (blacklist).</p>

        <div className="flex gap-2">
          <Input
            value={disallowedToolsInput}
            onChange={(e) => setDisallowedToolsInput(e.target.value)}
            placeholder="Enter tool pattern and press Add"
            disabled={isSubmitting}
            onKeyPress={(e) => {
              if (e.key === 'Enter') {
                e.preventDefault();
                handleAddDisallowedTool();
              }
            }}
          />
          <Button
            type="button"
            onClick={handleAddDisallowedTool}
            disabled={isSubmitting || !disallowedToolsInput.trim()}
            variant="outline"
          >
            Add
          </Button>
        </div>

        {disallowedTools.length > 0 && (
          <div className="flex flex-wrap gap-2">
            {disallowedTools.map((tool) => (
              <div
                key={tool}
                className="inline-flex items-center gap-2 rounded-full bg-red-100 px-3 py-1 text-sm text-red-900"
              >
                {tool}
                <button
                  type="button"
                  onClick={() => handleRemoveDisallowedTool(tool)}
                  className="hover:text-red-700"
                  disabled={isSubmitting}
                >
                  <X className="h-4 w-4" />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Actions */}
      <div className="flex justify-end gap-2">
        <Button
          type="button"
          variant="outline"
          onClick={onCancel}
          disabled={isSubmitting}
        >
          Cancel
        </Button>
        <Button type="submit" disabled={isSubmitting}>
          {isSubmitting ? 'Saving...' : initialData ? 'Update Tool Group' : 'Create Tool Group'}
        </Button>
      </div>
    </form>
  );
}
