import React from 'react';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '@/lib/utils';

const inputVariants = cva(
  'flex w-full rounded-md border border-border bg-surface px-3 py-2 text-body-large text-text-primary placeholder:text-text-tertiary focus:outline-none focus:ring-2 focus:ring-border-focus focus:border-transparent disabled:cursor-not-allowed disabled:opacity-50 transition-colors',
  {
    variants: {
      variant: {
        default: 'border-border',
        error: 'border-border-error focus:ring-border-error',
        success: 'border-border-success focus:ring-border-success',
        warning: 'border-border-warning focus:ring-border-warning',
      },
      size: {
        sm: 'h-9 px-3 text-body-medium',
        md: 'h-11 px-3 text-body-large',
        lg: 'h-12 px-4 text-title-small',
      },
    },
    defaultVariants: {
      variant: 'default',
      size: 'md',
    },
  }
);

export interface InputProps
  extends React.InputHTMLAttributes<HTMLInputElement>,
    VariantProps<typeof inputVariants> {
  label?: string;
  error?: string;
  help?: string;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
}

const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, variant, size, label, error, help, leftIcon, rightIcon, ...props }, ref) => {
    const inputId = React.useId();
    const errorId = React.useId();
    const helpId = React.useId();

    return (
      <div className="space-y-2">
        {label && (
          <label
            htmlFor={inputId}
            className="text-label-large font-medium text-text-primary"
          >
            {label}
            {props.required && <span className="text-error-500 ml-1">*</span>}
          </label>
        )}
        <div className="relative">
          {leftIcon && (
            <div className="absolute left-3 top-1/2 -translate-y-1/2 text-text-tertiary">
              {leftIcon}
            </div>
          )}
          <input
            id={inputId}
            className={cn(
              inputVariants({ variant, size, className }),
              leftIcon && 'pl-10',
              rightIcon && 'pr-10'
            )}
            ref={ref}
            aria-describedby={error ? errorId : help ? helpId : undefined}
            aria-invalid={error ? 'true' : 'false'}
            {...props}
          />
          {rightIcon && (
            <div className="absolute right-3 top-1/2 -translate-y-1/2 text-text-tertiary">
              {rightIcon}
            </div>
          )}
        </div>
        {error && (
          <p id={errorId} className="text-label-medium text-error-500">
            {error}
          </p>
        )}
        {help && !error && (
          <p id={helpId} className="text-label-medium text-text-tertiary">
            {help}
          </p>
        )}
      </div>
    );
  }
);

Input.displayName = 'Input';

export { Input, inputVariants };