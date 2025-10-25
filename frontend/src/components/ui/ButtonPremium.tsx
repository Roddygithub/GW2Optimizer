import type { ButtonHTMLAttributes, ReactNode } from 'react';
import type { LucideIcon } from 'lucide-react';
import { Loader2 } from 'lucide-react';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost';
  icon?: LucideIcon;
  children: ReactNode;
  isLoading?: boolean;
}

export const Button = ({
  children,
  onClick,
  variant = 'primary',
  className = '',
  disabled = false,
  icon: Icon,
  isLoading = false,
  ...props
}: ButtonProps) => {
  const baseStyle = `
    px-4 py-2 rounded-md text-sm font-medium font-serif tracking-wide 
    transition-all duration-200 flex items-center justify-center 
    focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-gw-dark
    disabled:cursor-not-allowed
  `;

  const variants = {
    primary: `
      bg-gw-red text-white 
      hover:bg-gw-red-dark hover:shadow-lg hover:scale-105
      focus:ring-gw-red
      disabled:bg-gw-gray disabled:text-gw-dark-secondary disabled:hover:scale-100
    `,
    secondary: `
      bg-gw-dark-secondary text-gw-gray 
      border border-gw-gray/50
      hover:text-gw-offwhite hover:border-gw-offwhite hover:border-gw-gold/50
      focus:ring-gw-gray
      disabled:opacity-50 disabled:hover:border-gw-gray/50
    `,
    ghost: `
      bg-transparent text-gw-gray
      hover:bg-gw-dark-secondary hover:text-gw-offwhite
      focus:ring-gw-gray
      disabled:opacity-50
    `,
  };

  return (
    <button
      onClick={onClick}
      disabled={disabled || isLoading}
      className={`${baseStyle} ${variants[variant]} ${className}`}
      {...props}
    >
      {isLoading ? (
        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
      ) : (
        Icon && <Icon className="h-4 w-4 mr-2" />
      )}
      {children}
    </button>
  );
};
