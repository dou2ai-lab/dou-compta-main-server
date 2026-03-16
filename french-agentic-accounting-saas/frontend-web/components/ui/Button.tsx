'use client'

import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { IconDefinition } from '@fortawesome/fontawesome-svg-core'
import { ReactNode } from 'react'

interface ButtonProps {
  children: ReactNode
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost'
  size?: 'sm' | 'md' | 'lg'
  icon?: IconDefinition
  iconPosition?: 'left' | 'right'
  className?: string
  onClick?: () => void
  type?: 'button' | 'submit' | 'reset'
  disabled?: boolean
}

export default function Button({
  children,
  variant = 'primary',
  size = 'md',
  icon,
  iconPosition = 'right',
  className = '',
  onClick,
  type = 'button',
  disabled = false,
}: ButtonProps) {
  const baseStyles = 'font-medium transition-all flex items-center justify-center space-x-2'
  
  const variantStyles = {
    primary: 'bg-primary hover:bg-primaryHover text-white',
    secondary: 'bg-gray-100 hover:bg-gray-200 text-textPrimary',
    outline: 'border border-borderColor hover:bg-gray-50 text-textPrimary',
    ghost: 'hover:bg-gray-50 text-textSecondary',
  }
  
  const sizeStyles = {
    sm: 'h-8 px-3 text-xs',
    md: 'h-10 px-4 text-sm',
    lg: 'h-12 px-6 text-sm',
  }
  
  const iconElement = icon && <FontAwesomeIcon icon={icon} />
  
  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled}
      className={`${baseStyles} ${variantStyles[variant]} ${sizeStyles[size]} ${className} ${
        disabled ? 'opacity-50 cursor-not-allowed' : ''
      }`}
    >
      {icon && iconPosition === 'left' && iconElement}
      <span>{children}</span>
      {icon && iconPosition === 'right' && iconElement}
    </button>
  )
}
