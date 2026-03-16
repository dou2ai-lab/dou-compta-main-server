'use client'

import { useState, useRef, useEffect } from 'react'
import { useLanguage } from '@/contexts/LanguageContext'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { faChevronDown } from '@fortawesome/free-solid-svg-icons'

const FR_FLAG = 'https://flagcdn.com/w40/fr.png'
const UK_FLAG = 'https://flagcdn.com/w40/gb.png'

type Variant = 'header' | 'compact'

export default function LanguageSwitcher({ variant = 'header' }: { variant?: Variant }) {
  const { locale, setLocale, t } = useLanguage()
  const [open, setOpen] = useState(false)
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (ref.current && !ref.current.contains(event.target as Node)) setOpen(false)
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const isCompact = variant === 'compact'

  return (
    <div className="relative" ref={ref}>
      <button
        type="button"
        onClick={(e) => { e.stopPropagation(); setOpen((o) => !o); }}
        className={`flex items-center space-x-2 rounded-lg border border-borderColor hover:bg-gray-50 transition-colors ${
          isCompact ? 'px-3 py-2' : 'px-3 py-2'
        }`}
        aria-label={t('header.language')}
        aria-expanded={open}
      >
        <img
          src={locale === 'fr' ? FR_FLAG : UK_FLAG}
          alt=""
          className="w-5 h-4 rounded"
        />
        <span className="text-sm font-medium text-textPrimary">{locale.toUpperCase()}</span>
        <FontAwesomeIcon icon={faChevronDown} className={`text-xs text-textMuted transition-transform ${open ? 'rotate-180' : ''}`} />
      </button>
      {open && (
        <div
          className="absolute right-0 top-full mt-1 py-1 bg-surface border border-borderColor rounded-lg shadow-lg min-w-[140px] z-[9999]"
          role="listbox"
        >
          <button
            type="button"
            role="option"
            onClick={(e) => { e.stopPropagation(); setLocale('fr'); setOpen(false); }}
            className={`w-full flex items-center space-x-2 px-3 py-2 text-left text-sm hover:bg-gray-50 ${locale === 'fr' ? 'bg-indigo-50 text-primary font-medium' : 'text-textPrimary'}`}
          >
            <img src={FR_FLAG} alt="" className="w-5 h-4 rounded" />
            <span>{t('header.french')}</span>
          </button>
          <button
            type="button"
            role="option"
            onClick={(e) => { e.stopPropagation(); setLocale('en'); setOpen(false); }}
            className={`w-full flex items-center space-x-2 px-3 py-2 text-left text-sm hover:bg-gray-50 ${locale === 'en' ? 'bg-indigo-50 text-primary font-medium' : 'text-textPrimary'}`}
          >
            <img src={UK_FLAG} alt="" className="w-5 h-4 rounded" />
            <span>{t('header.english')}</span>
          </button>
        </div>
      )}
    </div>
  )
}
