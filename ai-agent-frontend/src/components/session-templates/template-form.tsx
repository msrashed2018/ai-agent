'use client';

import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { SessionTemplateCreateRequest, SessionTemplateUpdateRequest, SessionTemplateResponse } from '@/types/api';
import { useTemplateCategories } from '@/hooks/use-session-templates';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Loader2 } from 'lucide-react';
import { useState } from 'react';

const templateSchema = z.object({
  name: z.string().min(1, 'Name is required').max(255, 'Name is too long'),
  description: z.string().optional(),
  category: z.string().optional(),
  system_prompt: z.string().optional(),
  working_directory: z.string().optional(),
  allowed_tools: z.array(z.string()).optional(),
  is_public: z.boolean().default(false),
  is_organization_shared: z.boolean().default(false),
  tags: z.array(z.string()).optional(),
});

type TemplateFormData = z.infer<typeof templateSchema>;

interface TemplateFormProps {
  template?: SessionTemplateResponse;
  onSubmit: (data: SessionTemplateCreateRequest | SessionTemplateUpdateRequest) => Promise<void>;
  isSubmitting?: boolean;
  submitLabel?: string;
}

export function TemplateForm({ template, onSubmit, isSubmitting, submitLabel = 'Create Template' }: TemplateFormProps) {
  const categories = useTemplateCategories();
  const [tagInput, setTagInput] = useState('');
  const [toolInput, setToolInput] = useState('');

  const {
    register,
    handleSubmit,
    watch,
    setValue,
    formState: { errors },
  } = useForm<TemplateFormData>({
    resolver: zodResolver(templateSchema),
    defaultValues: template ? {
      name: template.name,
      description: template.description || '',
      category: template.category || '',
      system_prompt: template.system_prompt || '',
      working_directory: template.working_directory || '',
      allowed_tools: template.allowed_tools || [],
      is_public: template.is_public,
      is_organization_shared: template.is_organization_shared,
      tags: template.tags || [],
    } : {
      name: '',
      description: '',
      category: '',
      system_prompt: '',
      working_directory: '',
      allowed_tools: [],
      is_public: false,
      is_organization_shared: false,
      tags: [],
    },
  });

  const tags = watch('tags') || [];
  const allowedTools = watch('allowed_tools') || [];
  const isPublic = watch('is_public');
  const isOrgShared = watch('is_organization_shared');

  const handleAddTag = () => {
    if (tagInput.trim() && !tags.includes(tagInput.trim())) {
      setValue('tags', [...tags, tagInput.trim()]);
      setTagInput('');
    }
  };

  const handleRemoveTag = (tag: string) => {
    setValue('tags', tags.filter((t) => t !== tag));
  };

  const handleAddTool = () => {
    if (toolInput.trim() && !allowedTools.includes(toolInput.trim())) {
      setValue('allowed_tools', [...allowedTools, toolInput.trim()]);
      setToolInput('');
    }
  };

  const handleRemoveTool = (tool: string) => {
    setValue('allowed_tools', allowedTools.filter((t) => t !== tool));
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
      {/* Basic Information */}
      <div className="space-y-4">
        <h3 className="text-lg font-medium">Basic Information</h3>

        <div className="space-y-2">
          <Label htmlFor="name">Template Name *</Label>
          <Input
            id="name"
            {...register('name')}
            placeholder="e.g., Python Development Setup"
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
            placeholder="What is this template for?"
            className="min-h-[80px]"
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="category">Category</Label>
          <Select
            value={watch('category')}
            onValueChange={(value) => setValue('category', value)}
          >
            <SelectTrigger id="category">
              <SelectValue placeholder="Select a category" />
            </SelectTrigger>
            <SelectContent>
              {categories.map((category) => (
                <SelectItem key={category} value={category} className="capitalize">
                  {category}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
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

      {/* Session Configuration */}
      <div className="space-y-4">
        <h3 className="text-lg font-medium">Session Configuration</h3>

        <div className="space-y-2">
          <Label htmlFor="system_prompt">System Prompt</Label>
          <Textarea
            id="system_prompt"
            {...register('system_prompt')}
            placeholder="Default system prompt for sessions created from this template"
            className="min-h-[120px] font-mono text-sm"
          />
          <p className="text-xs text-gray-500">
            This prompt will be used to initialize the AI assistant when creating a session from this template.
          </p>
        </div>

        <div className="space-y-2">
          <Label htmlFor="working_directory">Working Directory</Label>
          <Input
            id="working_directory"
            {...register('working_directory')}
            placeholder="/workspace/project"
            className="font-mono"
          />
          <p className="text-xs text-gray-500">
            Default working directory for sessions created from this template.
          </p>
        </div>

        <div className="space-y-2">
          <Label>Allowed Tools</Label>
          <div className="flex gap-2">
            <Input
              value={toolInput}
              onChange={(e) => setToolInput(e.target.value)}
              placeholder="Add tool name"
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  e.preventDefault();
                  handleAddTool();
                }
              }}
            />
            <Button type="button" onClick={handleAddTool}>Add</Button>
          </div>
          {allowedTools.length > 0 && (
            <div className="flex flex-wrap gap-2 mt-2">
              {allowedTools.map((tool) => (
                <span
                  key={tool}
                  className="bg-blue-100 text-blue-800 px-2 py-1 rounded-md text-sm flex items-center gap-1 font-mono"
                >
                  {tool}
                  <button
                    type="button"
                    onClick={() => handleRemoveTool(tool)}
                    className="text-blue-600 hover:text-blue-800"
                  >
                    ×
                  </button>
                </span>
              ))}
            </div>
          )}
          <p className="text-xs text-gray-500">
            Specify which tools the AI can use (e.g., bash, read_file, write_file).
          </p>
        </div>
      </div>

      {/* Sharing Settings */}
      <div className="space-y-4">
        <h3 className="text-lg font-medium">Sharing Settings</h3>

        <div className="flex items-center space-x-2">
          <Switch
            id="is_public"
            checked={isPublic}
            onCheckedChange={(checked: boolean) => setValue('is_public', checked)}
          />
          <Label htmlFor="is_public" className="cursor-pointer">
            Make this template public
          </Label>
        </div>
        <p className="text-sm text-gray-500 pl-6">
          Public templates can be discovered and used by anyone.
        </p>

        <div className="flex items-center space-x-2">
          <Switch
            id="is_organization_shared"
            checked={isOrgShared}
            onCheckedChange={(checked: boolean) => setValue('is_organization_shared', checked)}
          />
          <Label htmlFor="is_organization_shared" className="cursor-pointer">
            Share with organization
          </Label>
        </div>
        <p className="text-sm text-gray-500 pl-6">
          Organization-shared templates can be used by members of your organization.
        </p>
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
