'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { authAPI, getAuthErrorMessage } from '@/lib/api';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faEnvelope, faSpinner, faCheckCircle, faArrowLeft } from '@fortawesome/free-solid-svg-icons';

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [sent, setSent] = useState(false);
  const [resetToken, setResetToken] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    if (!email || !email.includes('@')) {
      setError('Veuillez entrer une adresse email valide.');
      return;
    }
    setLoading(true);
    try {
      const res = await authAPI.forgotPassword(email);
      setSent(true);
      if ((res as { reset_token?: string })?.reset_token) {
        setResetToken((res as { reset_token: string }).reset_token);
      }
    } catch (err: unknown) {
      if (process.env.NODE_ENV === 'development') console.error('Forgot password error:', err);
      setError(getAuthErrorMessage(err, 'Une erreur est survenue. Réessayez plus tard.'));
    } finally {
      setLoading(false);
    }
  };

  if (sent) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
        <div className="max-w-md w-full space-y-6 p-8 bg-white rounded-lg shadow-lg">
          <div className="text-center">
            <div className="inline-flex items-center justify-center w-16 h-16 bg-green-100 rounded-full mb-4">
              <FontAwesomeIcon icon={faCheckCircle} className="text-green-600 text-3xl" />
            </div>
            <h1 className="text-2xl font-bold text-gray-900">Email envoyé</h1>
            <p className="mt-2 text-gray-600">
              Si un compte existe avec cet email, vous recevrez un lien de réinitialisation.
            </p>
            {resetToken && (
              <p className="mt-4 text-sm text-gray-500">
                En mode développement, utilisez le lien ci-dessous pour réinitialiser votre mot de passe :
              </p>
            )}
            {resetToken && (
              <Link
                href={`/reset-password?token=${encodeURIComponent(resetToken)}`}
                className="mt-3 inline-block text-sm font-medium text-primary hover:text-primaryHover break-all"
              >
                Réinitialiser le mot de passe
              </Link>
            )}
          </div>
          <div className="text-center">
            <Link
              href="/login"
              className="inline-flex items-center gap-2 text-sm font-medium text-gray-600 hover:text-gray-900"
            >
              <FontAwesomeIcon icon={faArrowLeft} />
              Retour à la connexion
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
      <div className="max-w-md w-full space-y-8 p-8 bg-white rounded-lg shadow-lg">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 text-center">
            Mot de passe oublié
          </h1>
          <p className="mt-2 text-center text-sm text-gray-600">
            Entrez votre adresse email. Nous vous enverrons un lien pour réinitialiser votre mot de passe.
          </p>
        </div>
        <form className="space-y-6" onSubmit={handleSubmit}>
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-md text-sm">
              {error}
            </div>
          )}
          <div>
            <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1">
              Email
            </label>
            <div className="relative">
              <input
                id="email"
                name="email"
                type="email"
                autoComplete="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="vous@entreprise.com"
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:ring-primary focus:border-primary"
              />
              <FontAwesomeIcon
                icon={faEnvelope}
                className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400"
              />
            </div>
          </div>
          <button
            type="submit"
            disabled={loading}
            className="w-full flex justify-center items-center gap-2 py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-primary hover:bg-primaryHover focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary disabled:opacity-50"
          >
            {loading ? (
              <>
                <FontAwesomeIcon icon={faSpinner} className="animate-spin" />
                Envoi en cours...
              </>
            ) : (
              'Envoyer le lien'
            )}
          </button>
        </form>
        <div className="text-center">
          <Link
            href="/login"
            className="inline-flex items-center gap-2 text-sm font-medium text-gray-600 hover:text-gray-900"
          >
            <FontAwesomeIcon icon={faArrowLeft} />
            Retour à la connexion
          </Link>
        </div>
      </div>
    </div>
  );
}
