'use client';

import React, { useState, useEffect, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { authAPI, getAuthErrorMessage } from '@/lib/api';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faLock, faEye, faEyeSlash, faSpinner, faCheckCircle, faArrowLeft } from '@fortawesome/free-solid-svg-icons';

function ResetPasswordContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [token, setToken] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);

  useEffect(() => {
    const t = searchParams.get('token');
    if (t) setToken(t);
  }, [searchParams]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    if (!token) {
      setError('Lien de réinitialisation invalide ou expiré. Demandez un nouveau lien.');
      return;
    }
    if (newPassword.length < 8) {
      setError('Le mot de passe doit contenir au moins 8 caractères.');
      return;
    }
    if (!/[A-Za-z]/.test(newPassword)) {
      setError('Le mot de passe doit contenir au moins une lettre.');
      return;
    }
    if (!/\d/.test(newPassword)) {
      setError('Le mot de passe doit contenir au moins un chiffre.');
      return;
    }
    if (newPassword !== confirmPassword) {
      setError('Les mots de passe ne correspondent pas.');
      return;
    }
    setLoading(true);
    try {
      await authAPI.resetPassword(token, newPassword);
      setSuccess(true);
      setTimeout(() => router.push('/login'), 3000);
    } catch (err: unknown) {
      if (process.env.NODE_ENV === 'development') console.error('Reset password error:', err);
      setError(getAuthErrorMessage(err, 'Lien invalide ou expiré. Veuillez demander un nouveau lien.'));
    } finally {
      setLoading(false);
    }
  };

  if (success) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
        <div className="max-w-md w-full space-y-6 p-8 bg-white rounded-lg shadow-lg">
          <div className="text-center">
            <div className="inline-flex items-center justify-center w-16 h-16 bg-green-100 rounded-full mb-4">
              <FontAwesomeIcon icon={faCheckCircle} className="text-green-600 text-3xl" />
            </div>
            <h1 className="text-2xl font-bold text-gray-900">Mot de passe réinitialisé</h1>
            <p className="mt-2 text-gray-600">
              Votre mot de passe a été modifié. Vous allez être redirigé vers la page de connexion.
            </p>
          </div>
          <div className="text-center">
            <Link
              href="/login"
              className="inline-flex items-center gap-2 text-sm font-medium text-primary hover:text-primaryHover"
            >
              <FontAwesomeIcon icon={faArrowLeft} />
              Aller à la connexion
            </Link>
          </div>
        </div>
      </div>
    );
  }

  if (!token) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
        <div className="max-w-md w-full space-y-6 p-8 bg-white rounded-lg shadow-lg">
          <div className="text-center">
            <h1 className="text-2xl font-bold text-gray-900">Lien invalide</h1>
            <p className="mt-2 text-gray-600">
              Ce lien de réinitialisation est invalide ou expiré. Demandez un nouveau lien depuis la page « Mot de passe oublié ».
            </p>
          </div>
          <div className="text-center">
            <Link
              href="/forgot-password"
              className="inline-flex items-center gap-2 text-sm font-medium text-primary hover:text-primaryHover"
            >
              Demander un nouveau lien
            </Link>
            <span className="mx-2 text-gray-400">|</span>
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
            Nouveau mot de passe
          </h1>
          <p className="mt-2 text-center text-sm text-gray-600">
            Choisissez un mot de passe d&apos;au moins 8 caractères, avec des lettres et des chiffres.
          </p>
        </div>
        <form className="space-y-6" onSubmit={handleSubmit}>
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-md text-sm">
              {error}
            </div>
          )}
          <div>
            <label htmlFor="newPassword" className="block text-sm font-medium text-gray-700 mb-1">
              Nouveau mot de passe
            </label>
            <div className="relative">
              <input
                id="newPassword"
                name="newPassword"
                type={showPassword ? 'text' : 'password'}
                autoComplete="new-password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full pl-10 pr-10 py-2 border border-gray-300 rounded-md focus:ring-primary focus:border-primary"
              />
              <FontAwesomeIcon
                icon={faLock}
                className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400"
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
              >
                <FontAwesomeIcon icon={showPassword ? faEyeSlash : faEye} />
              </button>
            </div>
          </div>
          <div>
            <label htmlFor="confirmPassword" className="block text-sm font-medium text-gray-700 mb-1">
              Confirmer le mot de passe
            </label>
            <div className="relative">
              <input
                id="confirmPassword"
                name="confirmPassword"
                type={showPassword ? 'text' : 'password'}
                autoComplete="new-password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:ring-primary focus:border-primary"
              />
              <FontAwesomeIcon
                icon={faLock}
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
                Réinitialisation...
              </>
            ) : (
              'Réinitialiser le mot de passe'
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

export default function ResetPasswordPage() {
  return (
    <Suspense fallback={<div className="min-h-screen flex items-center justify-center bg-gray-50"><div className="animate-spin rounded-full h-10 w-10 border-2 border-primary border-t-transparent" /></div>}>
      <ResetPasswordContent />
    </Suspense>
  );
}
