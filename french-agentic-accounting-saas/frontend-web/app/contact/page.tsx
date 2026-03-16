'use client'

import { useState } from 'react'
import Link from 'next/link'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { faArrowLeft, faReceipt, faEnvelope, faPhone, faMapMarkerAlt, faPaperPlane } from '@fortawesome/free-solid-svg-icons'

export default function ContactPage() {
  const [form, setForm] = useState({ name: '', email: '', company: '', subject: '', message: '' })
  const [submitted, setSubmitted] = useState(false)

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setSubmitted(true)
  }

  return (
    <div className="min-h-screen bg-white">
      <header className="border-b border-gray-200 px-6 py-4">
        <div className="max-w-5xl mx-auto flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2">
            <div className="w-8 h-8 bg-indigo-600 rounded-lg flex items-center justify-center">
              <FontAwesomeIcon icon={faReceipt} className="text-white text-sm" />
            </div>
            <span className="text-lg font-semibold text-gray-900">DouCompta</span>
          </Link>
          <Link href="/" className="text-sm text-indigo-600 hover:underline flex items-center gap-1">
            <FontAwesomeIcon icon={faArrowLeft} className="text-xs" /> Retour
          </Link>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-6 py-12">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Contactez-nous</h1>
        <p className="text-gray-500 mb-10">Notre equipe est a votre disposition pour repondre a vos questions.</p>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-10">
          {/* Contact Info */}
          <div className="space-y-6">
            <div className="flex items-start gap-4">
              <div className="w-10 h-10 bg-indigo-50 rounded-lg flex items-center justify-center shrink-0">
                <FontAwesomeIcon icon={faMapMarkerAlt} className="text-indigo-600" />
              </div>
              <div>
                <h3 className="font-semibold text-gray-900 text-sm">Adresse</h3>
                <p className="text-gray-500 text-sm">12 Rue de la Paix<br />75002 Paris, France</p>
              </div>
            </div>
            <div className="flex items-start gap-4">
              <div className="w-10 h-10 bg-indigo-50 rounded-lg flex items-center justify-center shrink-0">
                <FontAwesomeIcon icon={faPhone} className="text-indigo-600" />
              </div>
              <div>
                <h3 className="font-semibold text-gray-900 text-sm">Telephone</h3>
                <p className="text-gray-500 text-sm">+33 1 42 00 00 00</p>
                <p className="text-gray-400 text-xs mt-0.5">Lun-Ven, 9h-18h</p>
              </div>
            </div>
            <div className="flex items-start gap-4">
              <div className="w-10 h-10 bg-indigo-50 rounded-lg flex items-center justify-center shrink-0">
                <FontAwesomeIcon icon={faEnvelope} className="text-indigo-600" />
              </div>
              <div>
                <h3 className="font-semibold text-gray-900 text-sm">Email</h3>
                <p className="text-gray-500 text-sm">contact@doucompta.fr</p>
                <p className="text-gray-500 text-sm">support@doucompta.fr</p>
              </div>
            </div>
          </div>

          {/* Form */}
          <div className="md:col-span-2">
            {submitted ? (
              <div className="bg-green-50 border border-green-200 rounded-xl p-8 text-center">
                <div className="text-green-600 text-4xl mb-4">&#10003;</div>
                <h3 className="text-lg font-semibold text-green-900 mb-2">Message envoye!</h3>
                <p className="text-green-700 text-sm">Nous vous repondrons dans les 24 heures.</p>
              </div>
            ) : (
              <form onSubmit={handleSubmit} className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Nom complet *</label>
                    <input type="text" required value={form.name} onChange={(e) => setForm({...form, name: e.target.value})}
                      className="w-full px-4 py-2.5 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 focus:border-transparent" />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Email *</label>
                    <input type="email" required value={form.email} onChange={(e) => setForm({...form, email: e.target.value})}
                      className="w-full px-4 py-2.5 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 focus:border-transparent" />
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Entreprise</label>
                  <input type="text" value={form.company} onChange={(e) => setForm({...form, company: e.target.value})}
                    className="w-full px-4 py-2.5 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 focus:border-transparent" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Sujet *</label>
                  <select required value={form.subject} onChange={(e) => setForm({...form, subject: e.target.value})}
                    className="w-full px-4 py-2.5 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 focus:border-transparent">
                    <option value="">Selectionnez...</option>
                    <option value="demo">Demande de demonstration</option>
                    <option value="pricing">Question tarifaire</option>
                    <option value="support">Support technique</option>
                    <option value="partnership">Partenariat</option>
                    <option value="other">Autre</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Message *</label>
                  <textarea required rows={5} value={form.message} onChange={(e) => setForm({...form, message: e.target.value})}
                    className="w-full px-4 py-2.5 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 focus:border-transparent resize-none" />
                </div>
                <button type="submit" className="w-full flex items-center justify-center gap-2 px-6 py-3 bg-indigo-600 text-white rounded-lg text-sm font-medium hover:bg-indigo-700 transition-colors">
                  <FontAwesomeIcon icon={faPaperPlane} /> Envoyer le message
                </button>
                <p className="text-xs text-gray-400 text-center">En soumettant ce formulaire, vous acceptez notre <Link href="/legal/confidentialite" className="text-indigo-600 hover:underline">politique de confidentialite</Link>.</p>
              </form>
            )}
          </div>
        </div>
      </main>

      <footer className="border-t border-gray-200 px-6 py-6">
        <div className="max-w-5xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-3 text-sm text-gray-400">
          <p>&copy; 2026 DouCompta SAS. Tous droits reserves.</p>
          <div className="flex gap-4">
            <Link href="/legal/mentions-legales" className="hover:text-gray-600">Mentions legales</Link>
            <Link href="/legal/cgu" className="hover:text-gray-600">CGU</Link>
            <Link href="/legal/confidentialite" className="hover:text-gray-600">Confidentialite</Link>
            <Link href="/legal/cookies" className="hover:text-gray-600">Cookies</Link>
          </div>
        </div>
      </footer>
    </div>
  )
}
