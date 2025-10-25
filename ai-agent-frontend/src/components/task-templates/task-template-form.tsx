'use client';

import { useState } from 'react';
import { TaskTemplateCreateRequest, TaskTemplateResponse } from '@/types/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Checkbox } from '@/components/ui/checkbox';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { ToolGroupSelector } from '@/components/tool-groups/tool-group-selector';
import { useToolGroups } from '@/hooks/use-tool-groups';
import { X, HelpCircle, AlertCircle } from 'lucide-react';

interface TaskTemplateFormProps {
  initialData?: TaskTemplateResponse | null;
  isSubmitting: boolean;
  onSubmit: (data: TaskTemplateCreateRequest) => void;
  onCancel: () => void;
}

export function TaskTemplateForm({
  initialData,
  isSubmitting,
  onSubmit,
  onCancel,
}: TaskTemplateFormProps) {
  const { data: toolGroupsData, isLoading: toolGroupsLoading } = useToolGroups();
  const toolGroups = toolGroupsData?.items || [];

  const [name, setName] = useState(initialData?.name || '');
  const [description, setDescription] = useState(initialData?.description || '');
  const [category, setCategory] = useState(initialData?.category || '');
  const [icon, setIcon] = useState(initialData?.icon || '');
  const [toolGroupId, setToolGroupId] = useState<string | undefined>(initialData?.tool_group_id || undefined);
  const [promptTemplate, setPromptTemplate] = useState(initialData?.prompt_template || '');
  const [templateVariablesSchema, setTemplateVariablesSchema] = useState(
    JSON.stringify(initialData?.template_variables_schema || {}, null, 2)
  );
  const [allowedToolsInput, setAllowedToolsInput] = useState('');
  const [allowedTools, setAllowedTools] = useState<string[]>(initialData?.allowed_tools || []);
  const [disallowedToolsInput, setDisallowedToolsInput] = useState('');
  const [disallowedTools, setDisallowedTools] = useState<string[]>(initialData?.disallowed_tools || []);
  const [sdkOptions, setSdkOptions] = useState(
    JSON.stringify(initialData?.sdk_options || {}, null, 2)
  );
  const [generateReport, setGenerateReport] = useState(initialData?.generate_report || false);
  const [reportFormat, setReportFormat] = useState(initialData?.report_format || '');
  const [tagsInput, setTagsInput] = useState('');
  const [tags, setTags] = useState<string[]>(initialData?.tags || []);
  const [isPublic, setIsPublic] = useState(initialData?.is_public || false);
  const [isActive, setIsActive] = useState(initialData?.is_active ?? true);

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

  const handleAddTag = () => {
    const tag = tagsInput.trim();
    if (tag && !tags.includes(tag)) {
      setTags([...tags, tag]);
      setTagsInput('');
    }
  };

  const handleRemoveTag = (tag: string) => {
    setTags(tags.filter((t) => t !== tag));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    if (!name.trim()) {
      alert('Task template name is required');
      return;
    }

    if (!promptTemplate.trim()) {
      alert('Prompt template is required');
      return;
    }

    // Parse and validate JSON fields
    let parsedVariablesSchema: Record<string, any> | undefined;
    let parsedSdkOptions: Record<string, any> | undefined;

    try {
      if (templateVariablesSchema.trim()) {
        parsedVariablesSchema = JSON.parse(templateVariablesSchema);
      }
    } catch (error) {
      alert('Invalid JSON in Template Variables Schema');
      return;
    }

    try {
      if (sdkOptions.trim()) {
        parsedSdkOptions = JSON.parse(sdkOptions);
      }
    } catch (error) {
      alert('Invalid JSON in SDK Options');
      return;
    }

    onSubmit({
      name: name.trim(),
      description: description.trim() || undefined,
      category: category.trim() || undefined,
      icon: icon.trim() || undefined,
      prompt_template: promptTemplate.trim(),
      template_variables_schema: parsedVariablesSchema,
      tool_group_id: toolGroupId || null,
      allowed_tools: allowedTools.length > 0 ? allowedTools : undefined,
      disallowed_tools: disallowedTools.length > 0 ? disallowedTools : undefined,
      sdk_options: parsedSdkOptions,
      generate_report: generateReport,
      report_format: reportFormat.trim() || undefined,
      tags: tags.length > 0 ? tags : undefined,
      is_public: isPublic,
      is_active: isActive,
    });
  };

  return (
    <TooltipProvider>
      <form onSubmit={handleSubmit} className="space-y-8">
        {/* Basic Info Section */}
        <div className="space-y-4">
          <div className="flex items-center gap-2 mb-4">
            <h3 className="text-lg font-semibold text-gray-900">Basic Information</h3>
            <Tooltip>
              <TooltipTrigger asChild>
                <HelpCircle className="h-4 w-4 text-gray-400 cursor-help" />
              </TooltipTrigger>
              <TooltipContent>Fill in the basic details about your task template</TooltipContent>
            </Tooltip>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Template Name <span className="text-red-500">*</span>
              </label>
              <Tooltip>
                <TooltipTrigger asChild>
                  <div className="relative">
                    <Input
                      value={name}
                      onChange={(e) => setName(e.target.value)}
                      placeholder="e.g., API Health Check, Database Migration"
                      disabled={isSubmitting}
                      className="pr-8"
                    />
                    <HelpCircle className="absolute right-2 top-2.5 h-4 w-4 text-gray-400 cursor-help" />
                  </div>
                </TooltipTrigger>
                <TooltipContent>
                  Use a descriptive name that clearly indicates what the task template does
                </TooltipContent>
              </Tooltip>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Category
              </label>
              <Tooltip>
                <TooltipTrigger asChild>
                  <div className="relative">
                    <Input
                      value={category}
                      onChange={(e) => setCategory(e.target.value)}
                      placeholder="e.g., DevOps, Monitoring, Security, Backup"
                      disabled={isSubmitting}
                      className="pr-8"
                    />
                    <HelpCircle className="absolute right-2 top-2.5 h-4 w-4 text-gray-400 cursor-help" />
                  </div>
                </TooltipTrigger>
                <TooltipContent>
                  Organize templates into categories for easier discovery and management
                </TooltipContent>
              </Tooltip>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Icon
            </label>
            <Tooltip>
              <TooltipTrigger asChild>
                <div className="relative">
                  <Input
                    value={icon}
                    onChange={(e) => setIcon(e.target.value)}
                    placeholder="e.g., 🚀 (emoji) or 🔧 (any unicode character)"
                    disabled={isSubmitting}
                    className="pr-8"
                  />
                  <HelpCircle className="absolute right-2 top-2.5 h-4 w-4 text-gray-400 cursor-help" />
                </div>
              </TooltipTrigger>
              <TooltipContent>
                Use any emoji or unicode character to represent this template visually
              </TooltipContent>
            </Tooltip>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Description
            </label>
            <Tooltip>
              <TooltipTrigger asChild>
                <div className="relative">
                  <Textarea
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    placeholder="e.g., Checks the health status of API endpoints and reports latency, error rates, and availability metrics..."
                    rows={3}
                    disabled={isSubmitting}
                    className="pr-8"
                  />
                  <HelpCircle className="absolute right-2 top-2.5 h-4 w-4 text-gray-400 cursor-help" />
                </div>
              </TooltipTrigger>
              <TooltipContent>
                Provide a clear description of what this template does and when to use it
              </TooltipContent>
            </Tooltip>
          </div>

          <div>
            <Tooltip>
              <TooltipTrigger asChild>
                <div>
                  <ToolGroupSelector
                    toolGroups={toolGroups}
                    value={toolGroupId}
                    onChange={setToolGroupId}
                    placeholder="Optional: Select a tool group to inherit tool restrictions"
                    disabled={isSubmitting || toolGroupsLoading}
                    isLoading={toolGroupsLoading}
                  />
                </div>
              </TooltipTrigger>
              <TooltipContent>
                Optionally associate this template with a tool group. The template will inherit the allowed and disallowed tools from the selected group.
              </TooltipContent>
            </Tooltip>
          </div>
        </div>

        {/* Prompt Template Section */}
        <div className="space-y-4 border-t pt-8">
          <div className="flex items-center gap-2 mb-4">
            <h3 className="text-lg font-semibold text-gray-900">Prompt Template</h3>
            <Tooltip>
              <TooltipTrigger asChild>
                <HelpCircle className="h-4 w-4 text-gray-400 cursor-help" />
              </TooltipTrigger>
              <TooltipContent>
                Define your prompt using Jinja2 syntax with variables like {`{{variable_name}}`}
              </TooltipContent>
            </Tooltip>
          </div>

          <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 mb-4">
            <p className="text-sm text-blue-800">
              💡 <strong>Tip:</strong> Use variables like {`{{service}}`}, {`{{environment}}`}, {`{{date}}`} in your prompt. They'll be replaced with actual values when executing the task.
            </p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Prompt <span className="text-red-500">*</span>
            </label>
            <Tooltip>
              <TooltipTrigger asChild>
                <Textarea
                  value={promptTemplate}
                  onChange={(e) => setPromptTemplate(e.target.value)}
                  placeholder={`Check the status of {{service}} in {{environment}} environment.\n\nProvide:\n1. Current health status\n2. Recent error logs (last 10 lines)\n3. Performance metrics\n4. Recommended actions if any issues found\n\nBe concise but thorough in your analysis.`}
                  rows={8}
                  disabled={isSubmitting}
                  className="font-mono text-sm"
                />
              </TooltipTrigger>
              <TooltipContent>
                Write your prompt here. Include variables for dynamic content that will be filled at execution time.
              </TooltipContent>
            </Tooltip>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Template Variables Schema <span className="text-gray-500">(JSON)</span>
            </label>
            <Tooltip>
              <TooltipTrigger asChild>
                <Textarea
                  value={templateVariablesSchema}
                  onChange={(e) => setTemplateVariablesSchema(e.target.value)}
                  placeholder={`{\n  "service": {\n    "type": "string",\n    "description": "Name of the service to check (e.g., api-server, database)"\n  },\n  "environment": {\n    "type": "string",\n    "description": "Environment name (e.g., production, staging, development)"\n  },\n  "depth": {\n    "type": "integer",\n    "description": "Analysis depth level (1-5)"\n  }\n}`}
                  rows={10}
                  disabled={isSubmitting}
                  className="font-mono text-xs bg-gray-50"
                />
              </TooltipTrigger>
              <TooltipContent>
                Define the schema for your template variables. This tells the system what inputs are needed when using this template.
              </TooltipContent>
            </Tooltip>
          </div>
        </div>

        {/* Allowed Tools Section */}
        <div className="space-y-4 border-t pt-8">
          <div className="flex items-center gap-2 mb-4">
            <h3 className="text-lg font-semibold text-gray-900">Allowed Tools</h3>
            <Tooltip>
              <TooltipTrigger asChild>
                <HelpCircle className="h-4 w-4 text-gray-400 cursor-help" />
              </TooltipTrigger>
              <TooltipContent>
                Whitelist of tools that can be used. Leave empty to allow all tools.
              </TooltipContent>
            </Tooltip>
          </div>

          <div className="bg-green-50 border border-green-200 rounded-lg p-3 mb-4">
            <p className="text-sm text-green-800">
              <strong>Examples:</strong> Bash(*), Bash(curl:*), Bash(kubectl get:*), Python(*), grep(*)
            </p>
          </div>

          <div className="flex gap-2">
            <Tooltip>
              <TooltipTrigger asChild>
                <Input
                  value={allowedToolsInput}
                  onChange={(e) => setAllowedToolsInput(e.target.value)}
                  placeholder="e.g., Bash(curl:*) or Bash(kubectl:*)"
                  disabled={isSubmitting}
                  onKeyPress={(e) => {
                    if (e.key === 'Enter') {
                      e.preventDefault();
                      handleAddAllowedTool();
                    }
                  }}
                />
              </TooltipTrigger>
              <TooltipContent>
                Enter a tool pattern and press Enter or click Add. Use wildcard (*) to allow all variants.
              </TooltipContent>
            </Tooltip>
            <Button
              type="button"
              onClick={handleAddAllowedTool}
              disabled={isSubmitting || !allowedToolsInput.trim()}
              className="bg-green-600 hover:bg-green-700"
            >
              Add
            </Button>
          </div>

          {allowedTools.length > 0 && (
            <div className="flex flex-wrap gap-2">
              {allowedTools.map((tool) => (
                <div
                  key={tool}
                  className="inline-flex items-center gap-2 rounded-full bg-green-100 px-4 py-2 text-sm font-medium text-green-900 hover:bg-green-200 transition-colors"
                >
                  <span>✓</span> {tool}
                  <button
                    type="button"
                    onClick={() => handleRemoveAllowedTool(tool)}
                    className="hover:text-green-700 ml-1"
                    disabled={isSubmitting}
                    title="Remove tool"
                  >
                    <X className="h-4 w-4" />
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Disallowed Tools Section */}
        <div className="space-y-4 border-t pt-8">
          <div className="flex items-center gap-2 mb-4">
            <h3 className="text-lg font-semibold text-gray-900">Disallowed Tools (Blacklist)</h3>
            <Tooltip>
              <TooltipTrigger asChild>
                <HelpCircle className="h-4 w-4 text-gray-400 cursor-help" />
              </TooltipTrigger>
              <TooltipContent>
                Tools that are NOT allowed to be used. Has priority over allowed tools.
              </TooltipContent>
            </Tooltip>
          </div>

          <div className="bg-red-50 border border-red-200 rounded-lg p-3 mb-4">
            <p className="text-sm text-red-800">
              <strong>Examples:</strong> Bash(rm:*), Bash(sudo:*), System(shutdown), System(reboot)
            </p>
          </div>

          <div className="flex gap-2">
            <Tooltip>
              <TooltipTrigger asChild>
                <Input
                  value={disallowedToolsInput}
                  onChange={(e) => setDisallowedToolsInput(e.target.value)}
                  placeholder="e.g., Bash(rm:*) or Bash(sudo:*)"
                  disabled={isSubmitting}
                  onKeyPress={(e) => {
                    if (e.key === 'Enter') {
                      e.preventDefault();
                      handleAddDisallowedTool();
                    }
                  }}
                />
              </TooltipTrigger>
              <TooltipContent>
                Enter a tool pattern to blacklist. These tools will never be allowed, even if in allowed list.
              </TooltipContent>
            </Tooltip>
            <Button
              type="button"
              onClick={handleAddDisallowedTool}
              disabled={isSubmitting || !disallowedToolsInput.trim()}
              className="bg-red-600 hover:bg-red-700"
            >
              Add
            </Button>
          </div>

          {disallowedTools.length > 0 && (
            <div className="flex flex-wrap gap-2">
              {disallowedTools.map((tool) => (
                <div
                  key={tool}
                  className="inline-flex items-center gap-2 rounded-full bg-red-100 px-4 py-2 text-sm font-medium text-red-900 hover:bg-red-200 transition-colors"
                >
                  <span>✗</span> {tool}
                  <button
                    type="button"
                    onClick={() => handleRemoveDisallowedTool(tool)}
                    className="hover:text-red-700 ml-1"
                    disabled={isSubmitting}
                    title="Remove tool"
                  >
                    <X className="h-4 w-4" />
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* SDK Options Section */}
        <div className="space-y-4 border-t pt-8">
          <div className="flex items-center gap-2 mb-4">
            <h3 className="text-lg font-semibold text-gray-900">SDK Options</h3>
            <Tooltip>
              <TooltipTrigger asChild>
                <HelpCircle className="h-4 w-4 text-gray-400 cursor-help" />
              </TooltipTrigger>
              <TooltipContent>
                Advanced options for the Claude SDK. Leave empty for default settings.
              </TooltipContent>
            </Tooltip>
          </div>

          <div className="bg-gray-50 border border-gray-200 rounded-lg p-3 mb-4">
            <p className="text-sm text-gray-700">
              <strong>Common options:</strong> max_tokens, temperature, top_p, system_prompt
            </p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              SDK Options <span className="text-gray-500">(JSON)</span>
            </label>
            <Tooltip>
              <TooltipTrigger asChild>
                <Textarea
                  value={sdkOptions}
                  onChange={(e) => setSdkOptions(e.target.value)}
                  placeholder={`{\n  "max_tokens": 4096,\n  "temperature": 0.7,\n  "top_p": 0.9\n}`}
                  rows={6}
                  disabled={isSubmitting}
                  className="font-mono text-xs bg-gray-50"
                />
              </TooltipTrigger>
              <TooltipContent>
                Additional SDK configuration options in JSON format. These control model behavior.
              </TooltipContent>
            </Tooltip>
          </div>
        </div>

        {/* Report Settings Section */}
        <div className="space-y-4 border-t pt-8">
          <div className="flex items-center gap-2 mb-4">
            <h3 className="text-lg font-semibold text-gray-900">Report Settings</h3>
            <Tooltip>
              <TooltipTrigger asChild>
                <HelpCircle className="h-4 w-4 text-gray-400 cursor-help" />
              </TooltipTrigger>
              <TooltipContent>
                Configure automatic report generation after task execution
              </TooltipContent>
            </Tooltip>
          </div>

          <div className="flex items-center space-x-3 p-3 bg-blue-50 border border-blue-200 rounded-lg">
            <Checkbox
              id="generate_report"
              checked={generateReport}
              onCheckedChange={(checked) => setGenerateReport(checked as boolean)}
              disabled={isSubmitting}
            />
            <label
              htmlFor="generate_report"
              className="text-sm font-medium text-gray-700 cursor-pointer"
            >
              Generate report after execution
            </label>
          </div>

          {generateReport && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Report Format
              </label>
              <Tooltip>
                <TooltipTrigger asChild>
                  <Input
                    value={reportFormat}
                    onChange={(e) => setReportFormat(e.target.value)}
                    placeholder="e.g., markdown, html, json, pdf"
                    disabled={isSubmitting}
                  />
                </TooltipTrigger>
                <TooltipContent>
                  Choose format: markdown (text), html (web), json (data), pdf (document)
                </TooltipContent>
              </Tooltip>
            </div>
          )}
        </div>

        {/* Tags Section */}
        <div className="space-y-4 border-t pt-8">
          <div className="flex items-center gap-2 mb-4">
            <h3 className="text-lg font-semibold text-gray-900">Tags</h3>
            <Tooltip>
              <TooltipTrigger asChild>
                <HelpCircle className="h-4 w-4 text-gray-400 cursor-help" />
              </TooltipTrigger>
              <TooltipContent>
                Add tags to help organize and discover templates
              </TooltipContent>
            </Tooltip>
          </div>

          <div className="flex gap-2">
            <Tooltip>
              <TooltipTrigger asChild>
                <Input
                  value={tagsInput}
                  onChange={(e) => setTagsInput(e.target.value)}
                  placeholder="e.g., monitoring, production, critical"
                  disabled={isSubmitting}
                  onKeyPress={(e) => {
                    if (e.key === 'Enter') {
                      e.preventDefault();
                      handleAddTag();
                    }
                  }}
                />
              </TooltipTrigger>
              <TooltipContent>
                Enter a tag and press Enter or click Add. Tags help with searching and filtering.
              </TooltipContent>
            </Tooltip>
            <Button
              type="button"
              onClick={handleAddTag}
              disabled={isSubmitting || !tagsInput.trim()}
              variant="outline"
            >
              Add Tag
            </Button>
          </div>

          {tags.length > 0 && (
            <div className="flex flex-wrap gap-2">
              {tags.map((tag) => (
                <div
                  key={tag}
                  className="inline-flex items-center gap-2 rounded-full bg-purple-100 px-4 py-2 text-sm font-medium text-purple-900 hover:bg-purple-200 transition-colors"
                >
                  #{tag}
                  <button
                    type="button"
                    onClick={() => handleRemoveTag(tag)}
                    className="hover:text-purple-700 ml-1"
                    disabled={isSubmitting}
                    title="Remove tag"
                  >
                    <X className="h-4 w-4" />
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Status Flags Section */}
        <div className="space-y-4 border-t pt-8">
          <div className="flex items-center gap-2 mb-4">
            <h3 className="text-lg font-semibold text-gray-900">Status & Visibility</h3>
            <Tooltip>
              <TooltipTrigger asChild>
                <HelpCircle className="h-4 w-4 text-gray-400 cursor-help" />
              </TooltipTrigger>
              <TooltipContent>
                Control template visibility and availability
              </TooltipContent>
            </Tooltip>
          </div>

          <div className="space-y-3">
            <div className="flex items-center space-x-3 p-3 bg-green-50 border border-green-200 rounded-lg hover:bg-green-100 transition-colors">
              <Checkbox
                id="is_active"
                checked={isActive}
                onCheckedChange={(checked) => setIsActive(checked as boolean)}
                disabled={isSubmitting}
              />
              <label
                htmlFor="is_active"
                className="text-sm font-medium text-gray-700 cursor-pointer flex-1"
              >
                <div className="font-semibold">Active</div>
                <div className="text-xs text-gray-600">Enable this template for use</div>
              </label>
            </div>

            <div className="flex items-center space-x-3 p-3 bg-blue-50 border border-blue-200 rounded-lg hover:bg-blue-100 transition-colors">
              <Checkbox
                id="is_public"
                checked={isPublic}
                onCheckedChange={(checked) => setIsPublic(checked as boolean)}
                disabled={isSubmitting}
              />
              <label
                htmlFor="is_public"
                className="text-sm font-medium text-gray-700 cursor-pointer flex-1"
              >
                <div className="font-semibold">Public</div>
                <div className="text-xs text-gray-600">Available to all users</div>
              </label>
            </div>
          </div>
        </div>

        {/* Actions Section */}
        <div className="flex justify-end gap-3 border-t pt-8">
          <Button
            type="button"
            variant="outline"
            onClick={onCancel}
            disabled={isSubmitting}
            className="px-6"
          >
            Cancel
          </Button>
          <Button
            type="submit"
            disabled={isSubmitting}
            className="px-8 bg-blue-600 hover:bg-blue-700"
          >
            {isSubmitting ? (
              <div className="flex items-center gap-2">
                <div className="h-4 w-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                Saving...
              </div>
            ) : initialData ? (
              '✓ Update Template'
            ) : (
              '+ Create Template'
            )}
          </Button>
        </div>
      </form>
    </TooltipProvider>
  );
}
