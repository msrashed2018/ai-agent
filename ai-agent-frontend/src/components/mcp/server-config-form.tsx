import { useState } from 'react';
import { MCPServerType } from '@/types/api';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { KeyValueEditor } from './key-value-editor';
import { Button } from '@/components/ui/button';
import { Plus, Trash2 } from 'lucide-react';

interface ServerConfigFormProps {
  serverType: MCPServerType;
  config: Record<string, any>;
  onChange: (config: Record<string, any>) => void;
}

export function ServerConfigForm({ serverType, config, onChange }: ServerConfigFormProps) {
  if (serverType === 'stdio') {
    return <StdioConfigForm config={config} onChange={onChange} />;
  }

  if (serverType === 'sse') {
    return <SSEConfigForm config={config} onChange={onChange} />;
  }

  if (serverType === 'http') {
    return <HTTPConfigForm config={config} onChange={onChange} />;
  }

  return null;
}

function StdioConfigForm({
  config,
  onChange,
}: {
  config: Record<string, any>;
  onChange: (config: Record<string, any>) => void;
}) {
  const args = config.args || [];
  const env = config.env || {};

  const handleArgsChange = (newArgs: string[]) => {
    onChange({ ...config, args: newArgs });
  };

  const handleEnvChange = (newEnv: Record<string, string>) => {
    onChange({ ...config, env: newEnv });
  };

  return (
    <div className="space-y-4">
      <div>
        <Label htmlFor="command">Command *</Label>
        <Input
          id="command"
          placeholder="e.g., npx, python, node"
          value={config.command || ''}
          onChange={(e) => onChange({ ...config, command: e.target.value })}
          required
        />
        <p className="text-xs text-gray-500 mt-1">The executable command to run</p>
      </div>

      <div>
        <Label>Arguments</Label>
        <ArgsEditor args={args} onChange={handleArgsChange} />
        <p className="text-xs text-gray-500 mt-1">Command line arguments (one per line)</p>
      </div>

      <KeyValueEditor
        label="Environment Variables"
        value={env}
        onChange={handleEnvChange}
        placeholder={{ key: 'VARIABLE_NAME', value: 'value' }}
      />
    </div>
  );
}

function SSEConfigForm({
  config,
  onChange,
}: {
  config: Record<string, any>;
  onChange: (config: Record<string, any>) => void;
}) {
  const headers = config.headers || {};

  return (
    <div className="space-y-4">
      <div>
        <Label htmlFor="url">URL *</Label>
        <Input
          id="url"
          type="url"
          placeholder="https://example.com/sse"
          value={config.url || ''}
          onChange={(e) => onChange({ ...config, url: e.target.value })}
          required
        />
        <p className="text-xs text-gray-500 mt-1">Server-sent events endpoint</p>
      </div>

      <KeyValueEditor
        label="Headers"
        value={headers}
        onChange={(newHeaders) => onChange({ ...config, headers: newHeaders })}
        placeholder={{ key: 'Header-Name', value: 'value' }}
      />
    </div>
  );
}

function HTTPConfigForm({
  config,
  onChange,
}: {
  config: Record<string, any>;
  onChange: (config: Record<string, any>) => void;
}) {
  const headers = config.headers || {};

  return (
    <div className="space-y-4">
      <div>
        <Label htmlFor="url">URL *</Label>
        <Input
          id="url"
          type="url"
          placeholder="https://api.example.com"
          value={config.url || ''}
          onChange={(e) => onChange({ ...config, url: e.target.value })}
          required
        />
        <p className="text-xs text-gray-500 mt-1">HTTP API endpoint</p>
      </div>

      <KeyValueEditor
        label="Headers"
        value={headers}
        onChange={(newHeaders) => onChange({ ...config, headers: newHeaders })}
        placeholder={{ key: 'Header-Name', value: 'value' }}
      />
    </div>
  );
}

function ArgsEditor({ args, onChange }: { args: string[]; onChange: (args: string[]) => void }) {
  const handleAdd = () => {
    onChange([...args, '']);
  };

  const handleRemove = (index: number) => {
    onChange(args.filter((_, i) => i !== index));
  };

  const handleChange = (index: number, value: string) => {
    const newArgs = [...args];
    newArgs[index] = value;
    onChange(newArgs);
  };

  return (
    <div className="space-y-2">
      {args.length === 0 ? (
        <div className="flex items-center justify-center py-4 border-2 border-dashed rounded-lg">
          <Button type="button" variant="outline" size="sm" onClick={handleAdd}>
            <Plus className="h-4 w-4 mr-1" />
            Add Argument
          </Button>
        </div>
      ) : (
        <>
          {args.map((arg, index) => (
            <div key={index} className="flex gap-2">
              <Input
                placeholder={`Argument ${index + 1}`}
                value={arg}
                onChange={(e) => handleChange(index, e.target.value)}
                className="flex-1"
              />
              <Button type="button" variant="outline" size="icon" onClick={() => handleRemove(index)}>
                <Trash2 className="h-4 w-4" />
              </Button>
            </div>
          ))}
          <Button type="button" variant="outline" size="sm" onClick={handleAdd} className="w-full">
            <Plus className="h-4 w-4 mr-1" />
            Add Argument
          </Button>
        </>
      )}
    </div>
  );
}
