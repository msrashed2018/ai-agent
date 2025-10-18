'use client';

import * as React from 'react';
import { useRouter } from 'next/navigation';
import { zodResolver } from '@hookform/resolvers/zod';
import { useForm } from 'react-hook-form';
import * as z from 'zod';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { useCreateSession } from '@/hooks/use-sessions';
import { Loader2 } from 'lucide-react';
import { apiClient } from '@/lib/api-client';
import { useQuery } from '@tanstack/react-query';

const sessionFormSchema = z.object({
  name: z.string().min(1, 'Name is required').max(100),
  description: z.string().optional(),
  model: z.string().min(1, 'Model is required'),
  system_prompt: z.string().optional(),
  allowed_tools: z.array(z.string()).optional(),
  mcp_servers: z.array(z.string()).optional(),
});

type SessionFormValues = z.infer<typeof sessionFormSchema>;

interface CreateSessionDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

const AVAILABLE_MODELS = [
  { value: 'claude-sonnet-4-5-20250929', label: 'Claude Sonnet 4.5 (Latest)' },
  { value: 'claude-3-5-sonnet-20241022', label: 'Claude 3.5 Sonnet' },
  { value: 'claude-3-opus-20240229', label: 'Claude 3 Opus' },
  { value: 'claude-3-haiku-20240307', label: 'Claude 3 Haiku' },
];

export function CreateSessionDialog({ open, onOpenChange }: CreateSessionDialogProps) {
  const router = useRouter();
  const createSession = useCreateSession();

  // Fetch MCP servers for selection
  const { data: mcpServersData } = useQuery({
    queryKey: ['mcp-servers'],
    queryFn: () => apiClient.listMCPServers(),
    enabled: open,
  });

  const {
    register,
    handleSubmit,
    formState: { errors },
    setValue,
    watch,
    reset,
  } = useForm<SessionFormValues>({
    resolver: zodResolver(sessionFormSchema),
    defaultValues: {
      name: '',
      description: '',
      model: 'claude-sonnet-4-5-20250929',
      system_prompt: '',
      allowed_tools: [],
      mcp_servers: [],
    },
  });

  const selectedModel = watch('model');
  const selectedMCPServers = watch('mcp_servers') || [];

  const onSubmit = async (data: SessionFormValues) => {
    try {
      const session = await createSession.mutateAsync({
        name: data.name,
        description: data.description || null,
        model: data.model,
        system_prompt: data.system_prompt || null,
        allowed_tools: data.allowed_tools || [],
        mcp_servers: data.mcp_servers || [],
      });

      reset();
      onOpenChange(false);
      router.push(`/sessions/${session.id}`);
    } catch (error) {
      // Error is handled by the mutation
    }
  };

  const toggleMCPServer = (serverId: string) => {
    const current = selectedMCPServers;
    if (current.includes(serverId)) {
      setValue(
        'mcp_servers',
        current.filter((id) => id !== serverId)
      );
    } else {
      setValue('mcp_servers', [...current, serverId]);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Create New Session</DialogTitle>
          <DialogDescription>
            Create a new AI agent session with custom configuration
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          {/* Name */}
          <div className="space-y-2">
            <Label htmlFor="name">
              Name <span className="text-red-500">*</span>
            </Label>
            <Input
              id="name"
              placeholder="My Session"
              {...register('name')}
              disabled={createSession.isPending}
            />
            {errors.name && (
              <p className="text-sm text-red-500">{errors.name.message}</p>
            )}
          </div>

          {/* Description */}
          <div className="space-y-2">
            <Label htmlFor="description">Description</Label>
            <Textarea
              id="description"
              placeholder="Optional description for this session"
              {...register('description')}
              disabled={createSession.isPending}
              rows={2}
            />
          </div>

          {/* Model */}
          <div className="space-y-2">
            <Label htmlFor="model">
              Model <span className="text-red-500">*</span>
            </Label>
            <Select
              value={selectedModel}
              onValueChange={(value) => setValue('model', value)}
              disabled={createSession.isPending}
            >
              <SelectTrigger>
                <SelectValue placeholder="Select a model" />
              </SelectTrigger>
              <SelectContent>
                {AVAILABLE_MODELS.map((model) => (
                  <SelectItem key={model.value} value={model.value}>
                    {model.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            {errors.model && (
              <p className="text-sm text-red-500">{errors.model.message}</p>
            )}
          </div>

          {/* System Prompt */}
          <div className="space-y-2">
            <Label htmlFor="system_prompt">System Prompt</Label>
            <Textarea
              id="system_prompt"
              placeholder="Optional system prompt to customize agent behavior"
              {...register('system_prompt')}
              disabled={createSession.isPending}
              rows={4}
            />
            <p className="text-xs text-gray-500">
              Define custom instructions for the AI agent
            </p>
          </div>

          {/* MCP Servers */}
          {mcpServersData && mcpServersData.items.length > 0 && (
            <div className="space-y-2">
              <Label>MCP Servers</Label>
              <div className="border rounded-md p-3 space-y-2 max-h-48 overflow-y-auto">
                {mcpServersData.items
                  .filter((server) => server.is_enabled)
                  .map((server) => (
                    <label
                      key={server.id}
                      className="flex items-center gap-2 p-2 hover:bg-gray-50 rounded cursor-pointer"
                    >
                      <input
                        type="checkbox"
                        checked={selectedMCPServers.includes(server.id)}
                        onChange={() => toggleMCPServer(server.id)}
                        disabled={createSession.isPending}
                        className="rounded"
                      />
                      <div className="flex-1">
                        <p className="text-sm font-medium">{server.name}</p>
                        {server.description && (
                          <p className="text-xs text-gray-500">{server.description}</p>
                        )}
                      </div>
                    </label>
                  ))}
              </div>
              <p className="text-xs text-gray-500">
                Select MCP servers to enable additional tools and capabilities
              </p>
            </div>
          )}

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => {
                reset();
                onOpenChange(false);
              }}
              disabled={createSession.isPending}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={createSession.isPending}>
              {createSession.isPending && (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              )}
              Create Session
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
