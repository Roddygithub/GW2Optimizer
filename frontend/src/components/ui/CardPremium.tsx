import type { ReactNode } from 'react';

interface CardProps {
  children: ReactNode;
  className?: string;
}

export const Card = ({ children, className = '' }: CardProps) => (
  <div
    className={`
      bg-gw-dark-secondary/80 backdrop-blur-sm 
      border border-gw-gold/20 rounded-lg shadow-lg 
      transition-all duration-200 hover:border-gw-gold/40
      ${className}
    `}
  >
    {children}
  </div>
);

interface CardHeaderProps {
  title: string;
  subtitle?: string;
  children?: ReactNode;
}

export const CardHeader = ({ title, subtitle, children }: CardHeaderProps) => (
  <div className="flex justify-between items-start p-4 border-b border-gw-gold/10">
    <div>
      <h3 className="text-lg font-serif font-bold text-gw-offwhite tracking-wide">
        {title}
      </h3>
      {subtitle && (
        <p className="mt-1 text-sm text-gw-gray">{subtitle}</p>
      )}
    </div>
    {children && <div>{children}</div>}
  </div>
);

interface CardBodyProps {
  children: ReactNode;
  className?: string;
}

export const CardBody = ({ children, className = '' }: CardBodyProps) => (
  <div className={`p-4 ${className}`}>{children}</div>
);

interface CardFooterProps {
  children: ReactNode;
  className?: string;
}

export const CardFooter = ({ children, className = '' }: CardFooterProps) => (
  <div
    className={`p-4 border-t border-gw-gold/10 bg-black/10 rounded-b-lg ${className}`}
  >
    {children}
  </div>
);
