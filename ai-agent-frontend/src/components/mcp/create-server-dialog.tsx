'use client';

import { useState } from 'react';
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
import { Switch } from '@/components/ui/switch';
import { TypeSelector } from './type-selector';
import { ServerConfigForm } from './server-config-form';
import { MCPServerType, MCPServerCreateRequest } from '@/types/api';
import { useCreateMCPServer } from '@/hooks/use-mcp-servers';
import { ChevronLeft, ChevronRight, Check, Loader2 } from 'lucide-react';

interface CreateServerDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  template?: {
    name: string;
    server_type: MCPServerType;
    config: Record<string, any>;
    description?: string;
  };
}

export function CreateServerDialog({ open, onOpenChange, template }: CreateServerDialogProps) {
  const [step, setStep] = useState(1);
  const [serverType, setServerType] = useState<MCPServerType | null>(
    template?.server_type || null
  );
  const [config, setConfig] = useState<Record<string, any>>(template?.config || {});
  const [name, setName] = useState(template?.name || '');
  const [description, setDescription] = useState(template?.description || '');
  const [enabled, setEnabled] = useState(true);

  const createMutation = useCreateMCPServer();

  const handleClose = () => {
    setStep(1);
    setServerType(template?.server_type || null);
    setConfig(template?.config || {});
    setName(template?.name || '');
    setDescription(template?.description || '');
    setEnabled(true);
    onOpenChange(false);
  };

  const handleNext = () => {
    if (step === 1 && serverType) {
      setStep(2);
    } else if (step === 2 && validateConfig()) {
      setStep(3);
    }
  };

  const handleBack = () => {
    if (step > 1) {
      setStep(step - 1);
    }
  };

  const validateConfig = (): boolean => {
    if (!serverType) return false;

    if (serverType === 'stdio') {
      return !!config.command;
    }

    if (serverType === 'sse' || serverType === 'http') {
      return !!config.url;
    }

    return false;
  };

  const handleSubmit = async () => {
    if (!serverType || !name) return;

    const data: MCPServerCreateRequest = {
      name,
      description: description || null,
      server_type: serverType,
      config,
      is_enabled: enabled,
    };

    await createMutation.mutateAsync(data);
    handleClose();
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Create MCP Server</DialogTitle>
          <DialogDescription>
            {step === 1 && 'Select the server type'}
            {step === 2 && 'Configure server connection'}
            {step === 3 && 'Name and configure server'}
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6">
          {/* Step Indicator */}
          <div className="flex items-center justify-center gap-2">
            {[1, 2, 3].map((s) => (
              <div
                key={s}
                className={`flex items-center justify-center w-8 h-8 rounded-full text-sm font-medium ${
                  s === step
                    ? 'bg-primary text-white'
                    : s < step
                    ? 'bg-green-600 text-white'
                    : 'bg-gray-200 text-gray-600'
                }`}
              >
                {s < step ? <Check className="h-4 w-4" /> : s}
              </div>
            ))}
          </div>

          {/* Step 1: Select Type */}
          {step === 1 && (
            <div>
              <TypeSelector selectedType={serverType} onSelect={setServerType} />
            </div>
          )}

          {/* Step 2: Configure */}
          {step === 2 && serverType && (
            <ServerConfigForm serverType={serverType} config={config} onChange={setConfig} />
          )}

          {/* Step 3: Name and Settings */}
          {step === 3 && (
            <div className="space-y-4">
              <div>
                <Label htmlFor="name">Name *</Label>
                <Input
                  id="name"
                  placeholder="e.g., filesystem-server"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  required
                />
              </div>

              <div>
                <Label htmlFor="description">Description</Label>
                <Textarea
                  id="description"
                  placeholder="Optional description of this server"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  rows={3}
                />
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <Label>Enable Server</Label>
                  <p className="text-xs text-gray-500">
                    Server will be available for use in sessions
                  </p>
                </div>
                <Switch checked={enabled} onCheckedChange={setEnabled} />
              </div>
            </div>
          )}
        </div>

        <DialogFooter>
          <div className="flex items-center justify-between w-full">
            <div>
              {step > 1 && (
                <Button type="button" variant="outline" onClick={handleBack}>
                  <ChevronLeft className="h-4 w-4 mr-1" />
                  Back
                </Button>
              )}
            </div>
            <div className="flex gap-2">
              <Button type="button" variant="outline" onClick={handleClose}>
                Cancel
              </Button>
              {step < 3 ? (
                <Button
                  type="button"
                  onClick={handleNext}
                  disabled={step === 1 ? !serverType : !validateConfig()}
                >
                  Next
                  <ChevronRight className="h-4 w-4 ml-1" />
                </Button>
              ) : (
                <Button
                  type="button"
                  onClick={handleSubmit}
                  disabled={!name || createMutation.isPending}
                >
                  {createMutation.isPending && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
                  Create Server
                </Button>
              )}
            </div>
          </div>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
