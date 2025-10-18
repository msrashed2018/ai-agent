import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { TaskCreateRequest, TaskUpdateRequest, TaskResponse } from '@/types/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { TemplateEditor } from './template-editor';
import { VariableEditor } from './variable-editor';
import { validateCron } from '@/lib/utils';
import { Loader2 } from 'lucide-react';
import { useState } from 'react';

const taskSchema = z.object({
  name: z.string().min(1, 'Name is required').max(255, 'Name is too long'),
  description: z.string().optional(),
  prompt_template: z.string().min(1, 'Prompt template is required'),
  template_variables: z.record(z.any()).optional(),
  is_scheduled: z.boolean().default(false),
  schedule_cron: z.string().optional(),
  schedule_enabled: z.boolean().default(false),
  generate_report: z.boolean().default(false),
  report_format: z.enum(['html', 'pdf', 'json', 'markdown']).optional(),
  tags: z.array(z.string()).optional(),
}).refine((data) => {
  if (data.is_scheduled && data.schedule_cron) {
    return validateCron(data.schedule_cron);
  }
  return true;
}, {
  message: 'Invalid cron expression. Use format: minute hour day month weekday',
  path: ['schedule_cron'],
});

type TaskFormData = z.infer<typeof taskSchema>;

interface TaskFormProps {
  task?: TaskResponse;
  onSubmit: (data: TaskCreateRequest | TaskUpdateRequest) => Promise<void>;
  isSubmitting?: boolean;
  submitLabel?: string;
}

export function TaskForm({ task, onSubmit, isSubmitting, submitLabel = 'Create Task' }: TaskFormProps) {
  const [tagInput, setTagInput] = useState('');

  const {
    register,
    handleSubmit,
    watch,
    setValue,
    formState: { errors },
  } = useForm<TaskFormData>({
    resolver: zodResolver(taskSchema),
    defaultValues: task ? {
      name: task.name,
      description: task.description || '',
      prompt_template: task.prompt_template,
      template_variables: task.template_variables,
      is_scheduled: task.is_scheduled,
      schedule_cron: task.schedule_cron || '',
      schedule_enabled: task.schedule_enabled,
      generate_report: task.generate_report,
      report_format: task.report_format || 'html',
      tags: task.tags || [],
    } : {
      name: '',
      description: '',
      prompt_template: '',
      template_variables: {},
      is_scheduled: false,
      schedule_cron: '',
      schedule_enabled: false,
      generate_report: false,
      report_format: 'html',
      tags: [],
    },
  });

  const promptTemplate = watch('prompt_template');
  const templateVariables = watch('template_variables') || {};
  const isScheduled = watch('is_scheduled');
  const generateReport = watch('generate_report');
  const tags = watch('tags') || [];

  const handleAddTag = () => {
    if (tagInput.trim() && !tags.includes(tagInput.trim())) {
      setValue('tags', [...tags, tagInput.trim()]);
      setTagInput('');
    }
  };

  const handleRemoveTag = (tag: string) => {
    setValue('tags', tags.filter((t) => t !== tag));
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
      {/* Basic Information */}
      <div className="space-y-4">
        <h3 className="text-lg font-medium">Basic Information</h3>

        <div className="space-y-2">
          <Label htmlFor="name">Task Name *</Label>
          <Input
            id="name"
            {...register('name')}
            placeholder="e.g., Daily Log Analysis"
          />
          {errors.name && (
            <p className="text-sm text-red-600">{errors.name.message}</p>
          )}
        </div>

        <div className="space-y-2">
          <Label htmlFor="description">Description</Label>
          <Textarea
            id="description"
            {...register('description')}
            placeholder="What does this task do?"
            className="min-h-[80px]"
          />
        </div>

        <div className="space-y-2">
          <Label>Tags</Label>
          <div className="flex gap-2">
            <Input
              value={tagInput}
              onChange={(e) => setTagInput(e.target.value)}
              placeholder="Add tag"
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  e.preventDefault();
                  handleAddTag();
                }
              }}
            />
            <Button type="button" onClick={handleAddTag}>Add</Button>
          </div>
          {tags.length > 0 && (
            <div className="flex flex-wrap gap-2 mt-2">
              {tags.map((tag) => (
                <span
                  key={tag}
                  className="bg-gray-100 text-gray-800 px-2 py-1 rounded-md text-sm flex items-center gap-1"
                >
                  {tag}
                  <button
                    type="button"
                    onClick={() => handleRemoveTag(tag)}
                    className="text-gray-500 hover:text-gray-700"
                  >
                    ×
                  </button>
                </span>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Prompt Template */}
      <div className="space-y-4">
        <h3 className="text-lg font-medium">Prompt Template</h3>
        <TemplateEditor
          value={promptTemplate}
          onChange={(value) => setValue('prompt_template', value)}
          variables={templateVariables}
          error={errors.prompt_template?.message}
        />
      </div>

      {/* Template Variables */}
      <div className="space-y-4">
        <h3 className="text-lg font-medium">Template Variables</h3>
        <p className="text-sm text-gray-500">
          Define default values for variables used in your prompt template
        </p>
        <VariableEditor
          variables={templateVariables}
          onChange={(vars) => setValue('template_variables', vars)}
        />
      </div>

      {/* Scheduling */}
      <div className="space-y-4">
        <h3 className="text-lg font-medium">Scheduling</h3>

        <div className="flex items-center space-x-2">
          <Switch
            id="is_scheduled"
            checked={isScheduled}
            onCheckedChange={(checked) => setValue('is_scheduled', checked)}
          />
          <Label htmlFor="is_scheduled">Enable scheduled execution</Label>
        </div>

        {isScheduled && (
          <div className="space-y-4 pl-6 border-l-2 border-gray-200">
            <div className="space-y-2">
              <Label htmlFor="schedule_cron">Cron Expression *</Label>
              <Input
                id="schedule_cron"
                {...register('schedule_cron')}
                placeholder="0 0 * * * (Daily at midnight)"
                className="font-mono"
              />
              {errors.schedule_cron && (
                <p className="text-sm text-red-600">{errors.schedule_cron.message}</p>
              )}
              <p className="text-xs text-gray-500">
                Format: minute hour day month weekday. Example: <code className="bg-gray-100 px-1 py-0.5 rounded">0 0 * * *</code> (daily at midnight)
              </p>
            </div>

            <div className="flex items-center space-x-2">
              <Switch
                id="schedule_enabled"
                checked={watch('schedule_enabled')}
                onCheckedChange={(checked) => setValue('schedule_enabled', checked)}
              />
              <Label htmlFor="schedule_enabled">Schedule enabled</Label>
            </div>
          </div>
        )}
      </div>

      {/* Report Generation */}
      <div className="space-y-4">
        <h3 className="text-lg font-medium">Report Generation</h3>

        <div className="flex items-center space-x-2">
          <Switch
            id="generate_report"
            checked={generateReport}
            onCheckedChange={(checked) => setValue('generate_report', checked)}
          />
          <Label htmlFor="generate_report">Generate report after execution</Label>
        </div>

        {generateReport && (
          <div className="space-y-2 pl-6 border-l-2 border-gray-200">
            <Label htmlFor="report_format">Report Format</Label>
            <Select
              value={watch('report_format')}
              onValueChange={(value) => setValue('report_format', value as any)}
            >
              <SelectTrigger id="report_format">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="html">HTML</SelectItem>
                <SelectItem value="pdf">PDF</SelectItem>
                <SelectItem value="json">JSON</SelectItem>
                <SelectItem value="markdown">Markdown</SelectItem>
              </SelectContent>
            </Select>
          </div>
        )}
      </div>

      {/* Submit Button */}
      <div className="flex justify-end gap-2 pt-4 border-t">
        <Button type="submit" disabled={isSubmitting}>
          {isSubmitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
          {submitLabel}
        </Button>
      </div>
    </form>
  );
}
