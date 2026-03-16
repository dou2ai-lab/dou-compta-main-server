'use client'

import { useState, useEffect, FormEvent } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { useAuth } from '@/contexts/AuthContext'
import { useLanguage } from '@/contexts/LanguageContext'
import { authAPI } from '@/lib/api'
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
  faExclamationCircle,
  faChevronDown,
  faStar,
  faUser,
} from '@fortawesome/free-solid-svg-icons'
import { faMicrosoft, faGoogle } from '@fortawesome/free-brands-svg-icons'

export default function SignupPage() {
  const router = useRouter()
  const { login, isAuthenticated } = useAuth()
  const { t, localeVersion } = useLanguage()
  void localeVersion

  const [firstName, setFirstName] = useState('')
  const [lastName, setLastName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [showConfirmPassword, setShowConfirmPassword] = useState(false)
  const [emailError, setEmailError] = useState(false)
  const [passwordError, setPasswordError] = useState(false)
  const [confirmError, setConfirmError] = useState(false)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [ssoRedirect, setSsoRedirect] = useState<{ show: boolean; provider: string }>({ show: false, provider: '' })
  const [ssoIconsMounted, setSsoIconsMounted] = useState(false)

  useEffect(() => {
    setSsoIconsMounted(true)
  }, [])

  useEffect(() => {
    if (isAuthenticated && !isSubmitting) {
      router.push('/expenses')
    }
  }, [isAuthenticated, isSubmitting, router])

  const handleTogglePassword = () => {
    setShowPassword(!showPassword)
  }

  const handleToggleConfirmPassword = () => {
    setShowConfirmPassword(!showConfirmPassword)
  }

  const handleSSO = (provider: string) => {
    setSsoRedirect({ show: true, provider })
    setTimeout(() => {
      setSsoRedirect({ show: false, provider: '' })
    }, 3000)
  }

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setEmailError(false)
    setPasswordError(false)
    setConfirmError(false)
    setErrorMessage(null)

    let isValid = true

    if (!email || !email.includes('@')) {
      setEmailError(true)
      isValid = false
    }

    if (!password || password.length < 8) {
      setPasswordError(true)
      isValid = false
    }

    if (!confirmPassword || confirmPassword !== password) {
      setConfirmError(true)
      isValid = false
    }

    if (!isValid) {
      return
    }

    try {
      setIsSubmitting(true)
      const response = await authAPI.signup(email, password, firstName || undefined, lastName || undefined)

      if (response.token && response.user) {
        if (typeof window !== 'undefined') {
          localStorage.setItem('token', response.token)
          if (response.refresh_token) {
            localStorage.setItem('refresh_token', response.refresh_token)
          }
          localStorage.setItem('user', JSON.stringify(response.user))

          const maxAge = 30 * 60
          const cookieString = `token=${encodeURIComponent(response.token)}; path=/; max-age=${maxAge}; SameSite=Lax`
          document.cookie = cookieString
        }

        await login(email, password)
        await new Promise((resolve) => setTimeout(resolve, 200))
        router.push('/expenses')
      } else {
        throw new Error('Réponse de création de compte invalide')
      }
    } catch (err: any) {
      setErrorMessage(err.response?.data?.detail || err.message || t('signup.createAccountError'))
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="flex h-screen bg-bgPage overflow-hidden">
      {/* Brand Panel - same as login */}
      <div className="w-[60%] gradient-brand relative overflow-hidden flex items-center justify-center p-16">
        <div className="absolute top-0 left-0 w-full h-full opacity-10">
          <div className="absolute top-20 left-20 w-64 h-64 bg-white rounded-full blur-3xl"></div>
          <div className="absolute bottom-20 right-20 w-96 h-96 bg-purple-300 rounded-full blur-3xl"></div>
          <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] bg-indigo-300 rounded-full blur-3xl"></div>
        </div>

        <div className="relative z-10 max-w-xl">
          <div className="mb-12">
            <div className="flex items-center space-x-4 mb-3">
              <div className="w-12 h-12 bg-white rounded-xl flex items-center justify-center">
                <FontAwesomeIcon icon={faReceipt} className="text-primary text-xl" />
              </div>
              <span className="text-white text-4xl font-bold">Dou</span>
            </div>
            <p className="text-indigo-100 text-sm">{t('signup.platformTagline')}</p>
          </div>

          <div className="mb-12">
            <h1 className="text-5xl font-bold text-white mb-4 leading-tight">{t('signup.title')}</h1>
            <p className="text-xl text-indigo-100">
              {t('signup.subtitle')}
            </p>
          </div>

          <div className="space-y-4 mb-12">
            <div className="feature-card rounded-xl p-5 flex items-start space-x-4">
              <div className="w-12 h-12 bg-white bg-opacity-20 rounded-lg flex items-center justify-center flex-shrink-0">
                <FontAwesomeIcon icon={faBrain} className="text-white text-xl" />
              </div>
              <div>
                <h3 className="text-white font-semibold text-lg mb-1">{t('signup.feature1Title')}</h3>
                <p className="text-indigo-100 text-sm">{t('signup.feature1Desc')}</p>
              </div>
            </div>

            <div className="feature-card rounded-xl p-5 flex items-start space-x-4">
              <div className="w-12 h-12 bg-white bg-opacity-20 rounded-lg flex items-center justify-center flex-shrink-0">
                <FontAwesomeIcon icon={faShield} className="text-white text-xl" />
              </div>
              <div>
                <h3 className="text-white font-semibold text-lg mb-1">{t('signup.feature2Title')}</h3>
                <p className="text-indigo-100 text-sm">{t('signup.feature2Desc')}</p>
              </div>
            </div>

            <div className="feature-card rounded-xl p-5 flex items-start space-x-4">
              <div className="w-12 h-12 bg-white bg-opacity-20 rounded-lg flex items-center justify-center flex-shrink-0">
                <FontAwesomeIcon icon={faChartLine} className="text-white text-xl" />
              </div>
              <div>
                <h3 className="text-white font-semibold text-lg mb-1">{t('signup.feature3Title')}</h3>
                <p className="text-indigo-100 text-sm">{t('signup.feature3Desc')}</p>
              </div>
            </div>
          </div>

          <div className="feature-card rounded-xl p-6">
            <div className="flex items-center space-x-4 mb-4">
              <img
                src="https://storage.googleapis.com/uxpilot-auth.appspot.com/avatars/avatar-2.jpg"
                alt="User"
                className="w-14 h-14 rounded-full border-2 border-white"
              />
              <div>
                <div className="text-white font-semibold">Jean Dupont</div>
                <div className="text-indigo-100 text-sm">{t('signup.testimonialRole')}</div>
              </div>
            </div>
            <p className="text-white text-sm italic">
              {t('signup.testimonialQuote')}
            </p>
            <div className="flex items-center space-x-1 mt-4">
              {[...Array(5)].map((_, i) => (
                <FontAwesomeIcon key={i} icon={faStar} className="text-yellow-300" />
              ))}
            </div>
          </div>

          {ssoIconsMounted && (
          <div className="absolute top-10 right-10 floating-animation">
            <div className="w-32 h-32 bg-white bg-opacity-10 rounded-3xl backdrop-blur-sm border border-white border-opacity-20 flex items-center justify-center">
              <FontAwesomeIcon icon={faReceipt} className="text-white text-4xl w-10 h-10 flex-shrink-0" />
            </div>
          </div>
          )}
        </div>
      </div>

      {/* Form Panel - styled like login, but for signup */}
      <div className="w-[40%] bg-surface flex items-center justify-center p-12 relative">
        <div className="absolute top-8 right-8 z-10">
          <LanguageSwitcher variant="compact" />
        </div>

        <div className="w-full max-w-md">
          <div className="text-center mb-8">
            <div className="inline-flex items-center justify-center w-16 h-16 bg-indigo-50 rounded-2xl mb-4">
              {ssoIconsMounted && <FontAwesomeIcon icon={faReceipt} className="text-primary text-2xl w-8 h-8 flex-shrink-0" />}
            </div>
            <h2 className="text-3xl font-bold text-textPrimary mb-2">{t('signup.welcome')}</h2>
            <p className="text-textSecondary">{t('signup.signUpToStart')}</p>
          </div>

          <div className="space-y-3 mb-6">
            <button
              onClick={() => handleSSO('Microsoft')}
              className="w-full h-12 flex items-center justify-center space-x-3 border-2 border-borderColor rounded-xl hover:bg-gray-50 transition-all font-medium text-textPrimary group"
            >
              {ssoIconsMounted && <FontAwesomeIcon icon={faMicrosoft} className="text-xl text-blue-600 w-5 h-5 flex-shrink-0" />}
              <span>{t('signup.continueWithMicrosoft')}</span>
            </button>
            <button
              onClick={() => handleSSO('Google')}
              className="w-full h-12 flex items-center justify-center space-x-3 border-2 border-borderColor rounded-xl hover:bg-gray-50 transition-all font-medium text-textPrimary group"
            >
              {ssoIconsMounted && <FontAwesomeIcon icon={faGoogle} className="text-xl text-red-500 w-5 h-5 flex-shrink-0" />}
              <span>{t('signup.continueWithGoogle')}</span>
            </button>

            <button
              onClick={() => handleSSO('Okta')}
              className="w-full h-12 flex items-center justify-center space-x-3 border-2 border-borderColor rounded-xl hover:bg-gray-50 transition-all font-medium text-textPrimary group"
            >
              {ssoIconsMounted && (
                <svg className="w-5 h-5 flex-shrink-0" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8zm-1-13h2v6h-2zm0 8h2v2h-2z" />
                </svg>
              )}
              <span>{t('signup.continueWithOkta') || 'Continuer avec Okta'}</span>
            </button>
          </div>

          {ssoIconsMounted && (
          <>
          <div className="relative mb-6">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-borderColor"></div>
            </div>
            <div className="relative flex justify-center text-sm">
              <span className="px-4 bg-surface text-textMuted">{t('signup.orContinueWithEmail')}</span>
            </div>
          </div>

          <form onSubmit={handleSubmit} className="space-y-5">
            {errorMessage && (
              <div className="p-4 bg-red-50 border border-errorRed rounded-xl">
                <div className="flex items-start space-x-3">
                  <FontAwesomeIcon icon={faExclamationCircle} className="text-errorRed text-lg mt-0.5 flex-shrink-0" />
                  <p className="text-sm text-textPrimary">{errorMessage}</p>
                </div>
              </div>
            )}

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label htmlFor="firstName" className="block text-sm font-medium text-textPrimary mb-2">
                  {t('signup.firstName')}
                </label>
                <div className="relative">
                  <input
                    type="text"
                    id="firstName"
                    name="firstName"
                    value={firstName}
                    onChange={(e) => setFirstName(e.target.value)}
                    placeholder={t('signup.firstNamePlaceholder')}
                    className="w-full h-12 pl-11 pr-4 border border-borderColor rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-all"
                  />
                  <FontAwesomeIcon icon={faUser} className="absolute left-4 top-1/2 transform -translate-y-1/2 text-textMuted" />
                </div>
              </div>
              <div>
                <label htmlFor="lastName" className="block text-sm font-medium text-textPrimary mb-2">
                  {t('signup.lastName')}
                </label>
                <div className="relative">
                  <input
                    type="text"
                    id="lastName"
                    name="lastName"
                    value={lastName}
                    onChange={(e) => setLastName(e.target.value)}
                    placeholder={t('signup.lastNamePlaceholder')}
                    className="w-full h-12 pl-11 pr-4 border border-borderColor rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-all"
                  />
                  <FontAwesomeIcon icon={faUser} className="absolute left-4 top-1/2 transform -translate-y-1/2 text-textMuted" />
                </div>
              </div>
            </div>

            <div>
              <label htmlFor="email" className="block text-sm font-medium text-textPrimary mb-2">
                {t('signup.email')}
              </label>
              <div className="relative">
                <input
                  type="email"
                  id="email"
                  name="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder={t('signup.emailPlaceholder')}
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
                <p className="text-xs text-errorRed mt-1">{t('signup.emailError')}</p>
              )}
            </div>

            <div>
              <label htmlFor="password" className="block text-sm font-medium text-textPrimary mb-2">
                {t('signup.password')}
              </label>
              <div className="relative">
                <input
                  type={showPassword ? 'text' : 'password'}
                  id="password"
                  name="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder={t('signup.passwordPlaceholder')}
                  className={`w-full h-12 pl-11 pr-12 border rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-all ${
                    passwordError ? 'border-errorRed' : 'border-borderColor'
                  }`}
                  required
                  minLength={8}
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
                <p className="text-xs text-errorRed mt-1">{t('signup.passwordError')}</p>
              )}
            </div>

            <div>
              <label htmlFor="confirmPassword" className="block text-sm font-medium text-textPrimary mb-2">
                {t('signup.confirmPassword')}
              </label>
              <div className="relative">
                <input
                  type={showConfirmPassword ? 'text' : 'password'}
                  id="confirmPassword"
                  name="confirmPassword"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder={t('signup.passwordPlaceholder')}
                  className={`w-full h-12 pl-11 pr-12 border rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-all ${
                    confirmError ? 'border-errorRed' : 'border-borderColor'
                  }`}
                  required
                  minLength={8}
                />
                {ssoIconsMounted && (
                  <FontAwesomeIcon
                    icon={faLock}
                    className="absolute left-4 top-1/2 transform -translate-y-1/2 text-textMuted w-4 h-4"
                  />
                )}
                <button
                  type="button"
                  onClick={handleToggleConfirmPassword}
                  className="password-toggle absolute right-4 top-1/2 transform -translate-y-1/2 text-textMuted"
                >
                  {ssoIconsMounted && <FontAwesomeIcon icon={showConfirmPassword ? faEyeSlash : faEye} className="w-4 h-4" />}
                </button>
              </div>
              {confirmError && (
                <p className="text-xs text-errorRed mt-1">{t('signup.confirmPasswordError')}</p>
              )}
            </div>

            {ssoRedirect.show && (
              <div className="p-4 bg-blue-50 border border-infoBlue rounded-xl">
                <div className="flex items-center space-x-3">
                  <div className="animate-spin">
                    <FontAwesomeIcon icon={faSpinner} className="text-infoBlue text-lg" />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-textPrimary">{t('signup.redirecting')}</p>
                    <p className="text-xs text-textSecondary mt-1">
                      {t('signup.redirectingDesc')} <span>{ssoRedirect.provider}</span>
                    </p>
                  </div>
                </div>
              </div>
            )}

            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full h-12 bg-primary hover:bg-primaryHover text-white rounded-xl font-semibold transition-all flex items-center justify-center space-x-2 disabled:opacity-50"
            >
              {isSubmitting ? (
                <>
                  <FontAwesomeIcon icon={faSpinner} className="animate-spin" />
                  <span>{t('signup.creatingAccount')}</span>
                </>
              ) : (
                <>
                  <span>{t('signup.createAccount')}</span>
                  {ssoIconsMounted && <FontAwesomeIcon icon={faArrowRight} className="w-4 h-4" />}
                </>
              )}
            </button>
          </form>

          <div className="mt-8 text-center">
            <p className="text-sm text-textSecondary">
              {t('signup.alreadyHaveAccount')}{' '}
              <Link href="/login" className="font-medium text-primary hover:text-primaryHover transition-colors">
                {t('signup.signIn')}
              </Link>
            </p>
          </div>

          <div className="mt-12 pt-8 border-t border-borderColor">
            <div className="flex items-center justify-center space-x-6 text-xs text-textMuted">
              <a href="#" className="hover:text-textPrimary transition-colors">
                {t('login.termsOfUse')}
              </a>
              <span>•</span>
              <a href="#" className="hover:text-textPrimary transition-colors">
                {t('login.privacyPolicy')}
              </a>
              <span>•</span>
              <a href="#" className="hover:text-textPrimary transition-colors">
                {t('login.support')}
              </a>
            </div>
            <p className="text-center text-xs text-textMuted mt-4">{t('login.copyright')}</p>
          </div>
          </>
          )}
        </div>
      </div>
    </div>
  )
}
