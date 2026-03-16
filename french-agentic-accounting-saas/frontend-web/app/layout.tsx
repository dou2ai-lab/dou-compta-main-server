// -----------------------------------------------------------------------------
// File: layout.tsx
// Company: Euron (A Subsidiary of EngageSphere Technology Private Limited)
// Created On: 21-11-2025
// Description: Root layout component with metadata and global styles
// -----------------------------------------------------------------------------

import type { Metadata } from 'next'
import Script from 'next/script'
import { Inter } from 'next/font/google'
import './globals.css'
import { AuthProviderWrapper } from '@/components/AuthProviderWrapper'
import { LanguageProvider } from '@/contexts/LanguageContext'
import AppLayoutWrapper from '@/components/AppLayoutWrapper'

// Optimize font loading with Next.js font optimization
const inter = Inter({
  subsets: ['latin'],
  weight: ['400', '500', '600', '700'],
  display: 'swap',
  preload: true,
  variable: '--font-inter',
  fallback: ['system-ui', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'sans-serif'],
})

export const metadata: Metadata = {
  title: 'Dou Expense & Audit AI - France Edition',
  description: 'AI-first expense management and audit platform',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="fr" className={inter.variable} suppressHydrationWarning>
      <body className={inter.className} suppressHydrationWarning>
        <Script
          id="prevent-fouc"
          strategy="beforeInteractive"
          dangerouslySetInnerHTML={{
            __html: `
              (function() {
                function markFontsLoaded() {
                  document.documentElement.classList.add('fonts-loaded');
                }
                if (document.fonts && document.fonts.ready) {
                  document.fonts.ready.then(function() {
                    markFontsLoaded();
                  }).catch(function() {
                    setTimeout(markFontsLoaded, 100);
                  });
                } else {
                  if (document.readyState === 'complete') {
                    setTimeout(markFontsLoaded, 0);
                  } else {
                    window.addEventListener('load', function() {
                      setTimeout(markFontsLoaded, 0);
                    });
                  }
                }
                if (document.readyState === 'loading') {
                  document.addEventListener('DOMContentLoaded', function() {
                    setTimeout(markFontsLoaded, 0);
                  });
                } else {
                  setTimeout(markFontsLoaded, 0);
                }
              })();
            `,
          }}
        />
        <AuthProviderWrapper>
          <LanguageProvider>
            <AppLayoutWrapper>
              {children}
            </AppLayoutWrapper>
          </LanguageProvider>
        </AuthProviderWrapper>
      </body>
    </html>
  )
}
