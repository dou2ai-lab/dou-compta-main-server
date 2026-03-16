'use client'

import { useState, useEffect, FormEvent, Suspense } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import Link from 'next/link'
import { useAuth } from '@/contexts/AuthContext'
import { useLanguage } from '@/contexts/LanguageContext'
import LanguageSwitcher from '@/components/LanguageSwitcher'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import {
  faReceipt,
  faBrain,
  faShield,
  faChartLine,
  faEnvelope,
  faLock,
  faEye,
  faEyeSlash,
  faArrowRight,
  faSpinner,
  faClock,
  faExclamationCircle,
  faChevronDown,
  faStar,
} from '@fortawesome/free-solid-svg-icons'
import {
  faMicrosoft,
  faGoogle,
} from '@fortawesome/free-brands-svg-icons'

const AUTH_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001'

function LoginContent() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const { login } = useAuth()
  const { t, localeVersion } = useLanguage()
  void localeVersion // force re-render when language changes
  const [showPassword, setShowPassword] = useState(false)
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [emailError, setEmailError] = useState(false)
  const [passwordError, setPasswordError] = useState(false)
  const [errorMessage, setErrorMessage] = useState(false)
  const [sessionExpired, setSessionExpired] = useState(searchParams.get('session') === 'expired')
  const [ssoRedirect, setSsoRedirect] = useState<{ show: boolean; provider: string }>({ show: false, provider: '' })
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [ssoIconsMounted, setSsoIconsMounted] = useState(false)

  useEffect(() => {
    setSsoIconsMounted(true)
  }, [])

  const handleTogglePassword = () => {
    setShowPassword(!showPassword)
  }

  const handleSSO = (provider: 'google' | 'microsoft' | 'okta') => {
    setSsoRedirect({ show: true, provider })
    const providerPath = provider
    if (typeof window !== 'undefined') {
      window.location.href = `${AUTH_BASE_URL}/api/v1/auth/oauth/${providerPath}/start`
    }
  }

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setEmailError(false)
    setPasswordError(false)
    setErrorMessage(false)

    let isValid = true

    if (!email || !email.includes('@')) {
      setEmailError(true)
      isValid = false
    }

    if (!password) {
      setPasswordError(true)
      isValid = false
    }

    if (!isValid) {
      return
    }

    try {
      setIsSubmitting(true)
      await login(email, password)
      // Small delay to ensure cookie and auth context are updated
      await new Promise((resolve) => setTimeout(resolve, 200))
      router.push('/dashboard')
    } catch (err) {
      setErrorMessage(true)
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="flex h-screen bg-bgPage overflow-hidden">
      {/* Brand Panel - hidden on mobile, scrollable on smaller desktops */}
      <div className="hidden lg:flex w-[55%] gradient-brand relative overflow-y-auto items-center justify-center p-10 xl:p-16">
        <div className="absolute top-0 left-0 w-full h-full opacity-10 pointer-events-none">
          <div className="absolute top-20 left-20 w-64 h-64 bg-white rounded-full blur-3xl"></div>
          <div className="absolute bottom-20 right-20 w-96 h-96 bg-purple-300 rounded-full blur-3xl"></div>
        </div>

        <div className="relative z-10 max-w-lg">
          <div className="mb-8">
            <div className="flex items-center space-x-3 mb-2">
              <div className="w-10 h-10 bg-white rounded-xl flex items-center justify-center">
                <FontAwesomeIcon icon={faReceipt} className="text-primary text-lg" />
              </div>
              <span className="text-white text-3xl font-bold">DouCompta</span>
            </div>
            <p className="text-indigo-200 text-sm">{t('login.platformTagline')}</p>
          </div>

          <div className="mb-8">
            <h1 className="text-3xl xl:text-4xl font-bold text-white mb-3 leading-tight">{t('login.title')}</h1>
            <p className="text-lg text-indigo-100">{t('login.subtitle')}</p>
          </div>

          <div className="space-y-3 mb-8">
            <div className="feature-card rounded-xl p-4 flex items-start space-x-3">
              <div className="w-10 h-10 bg-white bg-opacity-20 rounded-lg flex items-center justify-center flex-shrink-0">
                <FontAwesomeIcon icon={faBrain} className="text-white" />
              </div>
              <div>
                <h3 className="text-white font-semibold text-sm mb-0.5">{t('login.feature1Title')}</h3>
                <p className="text-indigo-200 text-xs">{t('login.feature1Desc')}</p>
              </div>
            </div>

            <div className="feature-card rounded-xl p-4 flex items-start space-x-3">
              <div className="w-10 h-10 bg-white bg-opacity-20 rounded-lg flex items-center justify-center flex-shrink-0">
                <FontAwesomeIcon icon={faShield} className="text-white" />
              </div>
              <div>
                <h3 className="text-white font-semibold text-sm mb-0.5">{t('login.feature2Title')}</h3>
                <p className="text-indigo-200 text-xs">{t('login.feature2Desc')}</p>
              </div>
            </div>

            <div className="feature-card rounded-xl p-4 flex items-start space-x-3">
              <div className="w-10 h-10 bg-white bg-opacity-20 rounded-lg flex items-center justify-center flex-shrink-0">
                <FontAwesomeIcon icon={faChartLine} className="text-white" />
              </div>
              <div>
                <h3 className="text-white font-semibold text-sm mb-0.5">{t('login.feature3Title')}</h3>
                <p className="text-indigo-200 text-xs">{t('login.feature3Desc')}</p>
              </div>
            </div>
          </div>

          <div className="feature-card rounded-xl p-5">
            <div className="flex items-center space-x-3 mb-3">
              <img
                src="https://storage.googleapis.com/uxpilot-auth.appspot.com/avatars/avatar-2.jpg"
                alt="User"
                className="w-11 h-11 rounded-full border-2 border-white"
              />
              <div>
                <div className="text-white font-semibold text-sm">Jean Dupont</div>
                <div className="text-indigo-200 text-xs">{t('login.testimonialRole')}</div>
              </div>
            </div>
            <p className="text-white text-xs italic leading-relaxed">
              {t('login.testimonialQuote')}
            </p>
            <div className="flex items-center space-x-1 mt-3">
              {[...Array(5)].map((_, i) => (
                <FontAwesomeIcon key={i} icon={faStar} className="text-yellow-300 text-xs" />
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Form Panel - full width on mobile, 45% on desktop */}
      <div className="w-full lg:w-[45%] bg-surface flex items-center justify-center p-6 sm:p-10 lg:p-12 relative overflow-y-auto">
        <div className="absolute top-8 right-8 z-10">
          <LanguageSwitcher variant="compact" />
        </div>
        <div className="w-full max-w-md">
          <div className="text-center mb-8">
            <div className="inline-flex items-center justify-center w-16 h-16 bg-indigo-50 rounded-2xl mb-4">
              {ssoIconsMounted && <FontAwesomeIcon icon={faReceipt} className="text-primary text-2xl w-8 h-8 flex-shrink-0" />}
            </div>
            <h2 className="text-3xl font-bold text-textPrimary mb-2">{t('login.welcome')}</h2>
            <p className="text-textSecondary">{t('login.signInToAccount')}</p>
          </div>

          <div className="space-y-3 mb-6">
            <button
              onClick={() => handleSSO('microsoft')}
              className="w-full h-12 flex items-center justify-center space-x-3 border-2 border-borderColor rounded-xl hover:bg-gray-50 transition-all font-medium text-textPrimary group"
            >
              {ssoIconsMounted && <FontAwesomeIcon icon={faMicrosoft} className="text-xl text-blue-600 w-5 h-5 flex-shrink-0" />}
              <span>{t('login.continueWithMicrosoft')}</span>
            </button>

            <button
              onClick={() => handleSSO('google')}
              className="w-full h-12 flex items-center justify-center space-x-3 border-2 border-borderColor rounded-xl hover:bg-gray-50 transition-all font-medium text-textPrimary group"
            >
              {ssoIconsMounted && <FontAwesomeIcon icon={faGoogle} className="text-xl text-red-500 w-5 h-5 flex-shrink-0" />}
              <span>{t('login.continueWithGoogle')}</span>
            </button>

            <button
              onClick={() => handleSSO('okta')}
              className="w-full h-12 flex items-center justify-center space-x-3 border-2 border-borderColor rounded-xl hover:bg-gray-50 transition-all font-medium text-textPrimary group"
            >
              {ssoIconsMounted && (
                <svg className="w-5 h-5 flex-shrink-0" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8zm-1-13h2v6h-2zm0 8h2v2h-2z" />
                </svg>
              )}
              <span>{t('login.continueWithOkta')}</span>
            </button>
          </div>

          {ssoIconsMounted && (
          <>
          <div className="relative mb-6">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-borderColor"></div>
            </div>
            <div className="relative flex justify-center text-sm">
              <span className="px-4 bg-surface text-textMuted">{t('login.orContinueWithEmail')}</span>
            </div>
          </div>

          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-textPrimary mb-2">
                {t('login.email')}
              </label>
              <div className="relative">
                <input
                  type="email"
                  id="email"
                  name="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder={t('login.emailPlaceholder')}
                  className={`w-full h-12 pl-11 pr-4 border rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-all ${
                    emailError ? 'border-errorRed' : 'border-borderColor'
                  }`}
                  required
                />
                {ssoIconsMounted && (
                  <FontAwesomeIcon
                    icon={faEnvelope}
                    className="absolute left-4 top-1/2 transform -translate-y-1/2 text-textMuted w-4 h-4"
                  />
                )}
              </div>
              {emailError && (
                <p className="text-xs text-errorRed mt-1">{t('login.emailError')}</p>
              )}
            </div>

            <div>
              <label htmlFor="password" className="block text-sm font-medium text-textPrimary mb-2">
                {t('login.password')}
              </label>
              <div className="relative">
                <input
                  type={showPassword ? 'text' : 'password'}
                  id="password"
                  name="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder={t('login.passwordPlaceholder')}
                  className={`w-full h-12 pl-11 pr-12 border rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-all ${
                    passwordError ? 'border-errorRed' : 'border-borderColor'
                  }`}
                  required
                />
                {ssoIconsMounted && (
                  <FontAwesomeIcon
                    icon={faLock}
                    className="absolute left-4 top-1/2 transform -translate-y-1/2 text-textMuted w-4 h-4"
                  />
                )}
                <button
                  type="button"
                  onClick={handleTogglePassword}
                  className="password-toggle absolute right-4 top-1/2 transform -translate-y-1/2 text-textMuted"
                >
                  {ssoIconsMounted && <FontAwesomeIcon icon={showPassword ? faEyeSlash : faEye} className="w-4 h-4" />}
                </button>
              </div>
              {passwordError && (
                <p className="text-xs text-errorRed mt-1">{t('login.passwordError')}</p>
              )}
            </div>

            <div className="flex items-center justify-between">
              <label className="flex items-center space-x-2 cursor-pointer">
                <input
                  type="checkbox"
                  id="remember"
                  className="w-4 h-4 text-primary border-borderColor rounded focus:ring-primary"
                />
                <span className="text-sm text-textSecondary">{t('login.rememberMe')}</span>
              </label>
              <a href="/forgot-password" className="text-sm font-medium text-primary hover:text-primaryHover transition-colors">
                {t('login.forgotPassword')}
              </a>
            </div>

            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full h-12 bg-primary hover:bg-primaryHover text-white rounded-xl font-semibold transition-all flex items-center justify-center space-x-2 disabled:opacity-50"
            >
              {isSubmitting ? (
                <>
                  <FontAwesomeIcon icon={faSpinner} className="animate-spin" />
                  <span>{t('login.signingIn')}</span>
                </>
              ) : (
                <>
                  <span>{t('login.signIn')}</span>
                  {ssoIconsMounted && <FontAwesomeIcon icon={faArrowRight} className="w-4 h-4" />}
                </>
              )}
            </button>

            {sessionExpired && (
              <div className="p-4 bg-amber-50 border border-warningAmber rounded-xl">
                <div className="flex items-start space-x-3">
                  <FontAwesomeIcon icon={faClock} className="text-warningAmber text-lg mt-0.5" />
                  <div>
                    <p className="text-sm font-medium text-textPrimary">{t('login.sessionExpired')}</p>
                    <p className="text-xs text-textSecondary mt-1">{t('login.sessionExpiredDesc')}</p>
                  </div>
                </div>
              </div>
            )}

            {errorMessage && (
              <div className="p-4 bg-red-50 border border-errorRed rounded-xl">
                <div className="flex items-start space-x-3">
                  <FontAwesomeIcon icon={faExclamationCircle} className="text-errorRed text-lg mt-0.5" />
                  <div>
                    <p className="text-sm font-medium text-textPrimary">{t('login.loginError')}</p>
                    <p className="text-xs text-textSecondary mt-1">{t('login.loginErrorDesc')}</p>
                  </div>
                </div>
              </div>
            )}

            {ssoRedirect.show && (
              <div className="p-4 bg-blue-50 border border-infoBlue rounded-xl">
                <div className="flex items-center space-x-3">
                  <div className="animate-spin">
                    <FontAwesomeIcon icon={faSpinner} className="text-infoBlue text-lg" />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-textPrimary">{t('login.redirecting')}</p>
                    <p className="text-xs text-textSecondary mt-1">
                      {t('login.redirectingDesc')} <span>{ssoRedirect.provider}</span>
                    </p>
                  </div>
                </div>
              </div>
            )}
          </form>

          <div className="mt-8 text-center">
            <p className="text-sm text-textSecondary">
              {t('login.noAccount')}{' '}
              <Link href="/signup" className="font-medium text-primary hover:text-primaryHover transition-colors">
                {t('login.createAccount')}
              </Link>
            </p>
          </div>

          <div className="mt-8 pt-6 border-t border-borderColor">
            <div className="flex items-center justify-center flex-wrap gap-4 text-xs text-textMuted">
              <Link href="/legal/cgu" className="hover:text-textPrimary transition-colors">
                {t('login.termsOfUse')}
              </Link>
              <span>•</span>
              <Link href="/legal/confidentialite" className="hover:text-textPrimary transition-colors">
                {t('login.privacyPolicy')}
              </Link>
              <span>•</span>
              <Link href="/contact" className="hover:text-textPrimary transition-colors">
                {t('login.support')}
              </Link>
            </div>
            <p className="text-center text-xs text-textMuted mt-3">{t('login.copyright')}</p>
          </div>
          </>
          )}
        </div>
      </div>
    </div>
  )
}

export default function LoginPage() {
  return (
    <Suspense fallback={<div className="min-h-screen flex items-center justify-center bg-bgPage"><div className="animate-spin rounded-full h-10 w-10 border-2 border-primary border-t-transparent" /></div>}>
      <LoginContent />
    </Suspense>
  )
}
