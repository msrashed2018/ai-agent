import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';

interface TemplateEditorProps {
  value: string;
  onChange: (value: string) => void;
  variables?: Record<string, any>;
  disabled?: boolean;
  error?: string;
}

export function TemplateEditor({ value, onChange, variables, disabled, error }: TemplateEditorProps) {
  // Extract variable names from template
  const templateVars = Array.from(value.matchAll(/\{\{(\w+)\}\}/g)).map((match) => match[1]);
  const uniqueVars = Array.from(new Set(templateVars));

  // Check for missing variables
  const definedVars = Object.keys(variables || {});
  const missingVars = uniqueVars.filter((v) => !definedVars.includes(v));
  const unusedVars = definedVars.filter((v) => !uniqueVars.includes(v));

  return (
    <div className="space-y-3">
      <div>
        <Label htmlFor="prompt-template" className="text-sm font-medium">
          Prompt Template
        </Label>
        <p className="text-xs text-gray-500 mt-1">
          Use <code className="bg-gray-100 px-1 py-0.5 rounded">{'{{variable_name}}'}</code> syntax for variables
        </p>
      </div>

      <Textarea
        id="prompt-template"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        disabled={disabled}
        className={`min-h-[200px] font-mono text-sm ${error ? 'border-red-500' : ''}`}
        placeholder="Enter your prompt template here...&#10;Example: Analyze the {{environment}} logs for {{service_name}}"
      />

      {error && <p className="text-sm text-red-600">{error}</p>}

      {uniqueVars.length > 0 && (
        <div className="flex flex-wrap gap-2 items-center">
          <span className="text-xs font-medium text-gray-600">Variables found:</span>
          {uniqueVars.map((v) => (
            <Badge
              key={v}
              variant="secondary"
              className={missingVars.includes(v) ? 'bg-yellow-100 text-yellow-800' : ''}
            >
              {v}
              {missingVars.includes(v) && ' ⚠'}
            </Badge>
          ))}
        </div>
      )}

      {missingVars.length > 0 && (
        <p className="text-xs text-yellow-600">
          ⚠ Missing default values for: {missingVars.join(', ')}
        </p>
      )}

      {unusedVars.length > 0 && (
        <p className="text-xs text-gray-500">
          ℹ Unused variables: {unusedVars.join(', ')}
        </p>
      )}
    </div>
  );
}
