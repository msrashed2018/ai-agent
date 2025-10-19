'use client';

import { useState } from 'react';
import { useSessionFork } from '@/hooks/use-sessions';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';

interface ForkSessionDialogProps {
  sessionId: string;
  onSuccess?: () => void;
}

export function ForkSessionDialog({ sessionId, onSuccess }: ForkSessionDialogProps) {
  const [open, setOpen] = useState(false);
  const [name, setName] = useState('');
  const [includeWorkdir, setIncludeWorkdir] = useState(true);
  const forkMutation = useSessionFork();

  const handleFork = async () => {
    try {
      await forkMutation.mutateAsync({
        sessionId,
        data: {
          name: name || null,
          include_working_directory: includeWorkdir,
        },
      });
      setOpen(false);
      onSuccess?.();
    } catch (error) {
      console.error('Fork error:', error);
    }
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button variant="outline">Fork Session</Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Fork Session</DialogTitle>
        </DialogHeader>
        <div className="space-y-4">
          <div>
            <Label htmlFor="fork-name">Session Name (Optional)</Label>
            <Input
              id="fork-name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="My Forked Session"
            />
          </div>
          <div className="flex items-center space-x-2">
            <Switch
              id="include-workdir"
              checked={includeWorkdir}
              onCheckedChange={setIncludeWorkdir}
            />
            <Label htmlFor="include-workdir">Include Working Directory Files</Label>
          </div>
          <Button onClick={handleFork} disabled={forkMutation.isPending} className="w-full">
            {forkMutation.isPending ? 'Forking...' : 'Fork Session'}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
