'use client';

import { LogOut, User, Settings } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/store/auth-store';
import { apiClient } from '@/lib/api-client';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';

function getUserInitials(email: string): string {
  const parts = email.split('@')[0].split('.');
  if (parts.length >= 2) {
    return (parts[0][0] + parts[1][0]).toUpperCase();
  }
  return email.slice(0, 2).toUpperCase();
}

export function UserMenu() {
  const router = useRouter();
  const { user, logout } = useAuthStore();

  const handleLogout = () => {
    apiClient.logout();
    logout();
    router.push('/auth/login');
  };

  if (!user) {
    return null;
  }

  const initials = getUserInitials(user.email);

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" className="relative h-10 w-10 rounded-full">
          <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary text-primary-foreground">
            {initials}
          </div>
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent className="w-56" align="end" forceMount>
        <DropdownMenuLabel className="font-normal">
          <div className="flex flex-col space-y-1">
            <p className="text-sm font-medium leading-none">{user.email}</p>
            <div className="flex items-center gap-2 mt-1">
              <Badge variant={user.role === 'admin' ? 'default' : 'secondary'} className="text-xs">
                {user.role}
              </Badge>
              {user.is_active && (
                <Badge variant="outline" className="text-xs">
                  Active
                </Badge>
              )}
            </div>
          </div>
        </DropdownMenuLabel>
        <DropdownMenuSeparator />
        <DropdownMenuItem disabled className="cursor-not-allowed opacity-50">
          <User className="mr-2 h-4 w-4" />
          <span>Profile</span>
        </DropdownMenuItem>
        <DropdownMenuItem disabled className="cursor-not-allowed opacity-50">
          <Settings className="mr-2 h-4 w-4" />
          <span>Settings</span>
        </DropdownMenuItem>
        <DropdownMenuSeparator />
        <DropdownMenuItem onClick={handleLogout} className="cursor-pointer text-red-600">
          <LogOut className="mr-2 h-4 w-4" />
          <span>Logout</span>
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
