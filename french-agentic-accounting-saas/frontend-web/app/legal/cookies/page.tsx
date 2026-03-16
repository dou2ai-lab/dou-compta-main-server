'use client'

import Link from 'next/link'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { faArrowLeft, faReceipt } from '@fortawesome/free-solid-svg-icons'

export default function CookiesPage() {
  return (
    <div className="min-h-screen bg-white">
      <header className="border-b border-gray-200 px-6 py-4">
        <div className="max-w-4xl mx-auto flex items-center justify-between">
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

      <main className="max-w-4xl mx-auto px-6 py-12">
        <h1 className="text-3xl font-bold text-gray-900 mb-8">Politique de Cookies</h1>

        <div className="prose prose-gray max-w-none space-y-8">
          <section>
            <h2 className="text-xl font-semibold text-gray-900 mb-3">1. Qu'est-ce qu'un cookie ?</h2>
            <p className="text-gray-600 leading-relaxed">Un cookie est un petit fichier texte depose sur votre terminal (ordinateur, tablette, telephone) lors de la visite d'un site web. Il permet au site de memoriser des informations sur votre visite, telles que votre langue preferee et d'autres parametres.</p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-gray-900 mb-3">2. Cookies utilises par DouCompta</h2>
            <div className="overflow-x-auto">
              <table className="w-full text-sm text-left border border-gray-200 rounded-lg overflow-hidden">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-3 font-semibold text-gray-700">Cookie</th>
                    <th className="px-4 py-3 font-semibold text-gray-700">Type</th>
                    <th className="px-4 py-3 font-semibold text-gray-700">Finalite</th>
                    <th className="px-4 py-3 font-semibold text-gray-700">Duree</th>
                  </tr>
                </thead>
                <tbody className="text-gray-600 divide-y divide-gray-200">
                  <tr><td className="px-4 py-3">token</td><td className="px-4 py-3">Essentiel</td><td className="px-4 py-3">Authentification utilisateur</td><td className="px-4 py-3">30 min</td></tr>
                  <tr><td className="px-4 py-3">refresh_token</td><td className="px-4 py-3">Essentiel</td><td className="px-4 py-3">Renouvellement de session</td><td className="px-4 py-3">7 jours</td></tr>
                  <tr><td className="px-4 py-3">locale</td><td className="px-4 py-3">Fonctionnel</td><td className="px-4 py-3">Preference de langue</td><td className="px-4 py-3">1 an</td></tr>
                </tbody>
              </table>
            </div>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-gray-900 mb-3">3. Cookies tiers</h2>
            <p className="text-gray-600 leading-relaxed">DouCompta n'utilise aucun cookie de tracking, de publicite ou de reseaux sociaux. Nous ne partageons aucune donnee avec des tiers via des cookies.</p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-gray-900 mb-3">4. Gestion des cookies</h2>
            <p className="text-gray-600 leading-relaxed">Vous pouvez configurer votre navigateur pour refuser les cookies. Cependant, le refus des cookies essentiels empechera l'utilisation du service. Pour gerer vos cookies : Parametres &gt; Confidentialite &gt; Cookies dans votre navigateur.</p>
          </section>
        </div>

        <div className="mt-12 pt-6 border-t border-gray-200">
          <p className="text-sm text-gray-400 mb-4">Derniere mise a jour : Mars 2026</p>
          <div className="flex flex-wrap gap-4 text-sm">
            <Link href="/legal/mentions-legales" className="text-indigo-600 hover:underline">Mentions legales</Link>
            <Link href="/legal/cgu" className="text-indigo-600 hover:underline">CGU</Link>
            <Link href="/legal/confidentialite" className="text-indigo-600 hover:underline">Confidentialite</Link>
            <Link href="/contact" className="text-indigo-600 hover:underline">Contact</Link>
          </div>
        </div>
      </main>

      <footer className="border-t border-gray-200 px-6 py-6 text-center text-sm text-gray-400">
        &copy; 2026 DouCompta SAS. Tous droits reserves.
      </footer>
    </div>
  )
}
