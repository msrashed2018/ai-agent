import { getInitials } from '@/lib/utils';

interface UserAvatarProps {
  email: string;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export function UserAvatar({ email, size = 'md', className = '' }: UserAvatarProps) {
  const initials = getInitials(email);

  const sizeClasses = {
    sm: 'h-8 w-8 text-xs',
    md: 'h-10 w-10 text-sm',
    lg: 'h-12 w-12 text-base',
  };

  // Generate a consistent color based on email
  const getColor = (str: string) => {
    const colors = [
      'bg-blue-500',
      'bg-green-500',
      'bg-purple-500',
      'bg-pink-500',
      'bg-indigo-500',
      'bg-yellow-500',
      'bg-red-500',
      'bg-teal-500',
    ];
    const index = str.charCodeAt(0) % colors.length;
    return colors[index];
  };

  return (
    <div
      className={`${sizeClasses[size]} ${getColor(email)} ${className} rounded-full flex items-center justify-center text-white font-semibold`}
    >
      {initials}
    </div>
  );
}
