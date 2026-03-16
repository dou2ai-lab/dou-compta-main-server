'use client'

import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { IconDefinition } from '@fortawesome/fontawesome-svg-core'
import { ReactNode } from 'react'

interface BadgeProps {
  children: ReactNode
  variant?: 'default' | 'success' | 'warning' | 'error' | 'info' | 'purple' | 'orange' | 'pink'
  icon?: IconDefinition
  className?: string
}

export default function Badge({
  children,
  variant = 'default',
  icon,
  className = '',
}: BadgeProps) {
  const variantStyles = {
    default: 'text-textMuted bg-gray-100',
    success: 'text-successGreen bg-green-50',
    warning: 'text-warningAmber bg-amber-50',
    error: 'text-errorRed bg-red-50',
    info: 'text-infoBlue bg-blue-50',
    purple: 'text-purple-600 bg-purple-50',
    orange: 'text-orange-600 bg-orange-50',
    pink: 'text-pink-600 bg-pink-50',
  }
  
  return (
    <span
      className={`inline-flex items-center text-xs font-medium px-2 py-1 rounded-full ${variantStyles[variant]} ${className}`}
    >
      {icon && <FontAwesomeIcon icon={icon} className="mr-1" />}
      {children}
    </span>
  )
}
