'use client'

import Link from 'next/link'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { faArrowLeft, faReceipt } from '@fortawesome/free-solid-svg-icons'

export default function CGUPage() {
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
        <h1 className="text-3xl font-bold text-gray-900 mb-8">Conditions Generales d'Utilisation</h1>

        <div className="prose prose-gray max-w-none space-y-8">
          <section>
            <h2 className="text-xl font-semibold text-gray-900 mb-3">Article 1 - Objet</h2>
            <p className="text-gray-600 leading-relaxed">Les presentes Conditions Generales d'Utilisation (CGU) regissent l'utilisation de la plateforme DouCompta, un service de comptabilite en ligne conforme au Plan Comptable General (PCG) 2025 et aux reglementations fiscales francaises. L'utilisation du service implique l'acceptation pleine et entiere des presentes CGU.</p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-gray-900 mb-3">Article 2 - Description du service</h2>
            <p className="text-gray-600 leading-relaxed">DouCompta fournit une plateforme SaaS de comptabilite automatisee incluant : la tenue comptable automatique (agent COMPTAA), le rapprochement bancaire intelligent (agent BANKA), les declarations fiscales automatisees (agent FISCA), l'analyse financiere (agents FINA/FORECASTA), la facturation electronique conforme Factur-X, et la collecte automatique de documents (agent CLASSA).</p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-gray-900 mb-3">Article 3 - Inscription et compte</h2>
            <p className="text-gray-600 leading-relaxed">L'acces au service necessite la creation d'un compte utilisateur. L'utilisateur s'engage a fournir des informations exactes et a maintenir la confidentialite de ses identifiants. Toute activite realisee depuis le compte de l'utilisateur est presumee etre de son fait.</p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-gray-900 mb-3">Article 4 - Conformite reglementaire</h2>
            <p className="text-gray-600 leading-relaxed">DouCompta s'engage a maintenir la conformite de son service avec : le Plan Comptable General (PCG) 2025, le Fichier des Ecritures Comptables (FEC) conforme a l'article A47 A-1 du LPF, les normes de facturation electronique (Factur-X / EN16931), et les obligations de declaration (CA3, IS, CVAE). L'utilisateur reste responsable de la verification et de la validation de ses ecritures comptables.</p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-gray-900 mb-3">Article 5 - Protection des donnees</h2>
            <p className="text-gray-600 leading-relaxed">DouCompta traite les donnees personnelles conformement au RGPD. Les donnees comptables sont hebergees exclusivement en France. L'utilisateur conserve la propriete de ses donnees et peut les exporter a tout moment au format FEC ou en CSV. Pour plus de details, consultez notre Politique de Confidentialite.</p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-gray-900 mb-3">Article 6 - Responsabilite</h2>
            <p className="text-gray-600 leading-relaxed">DouCompta met en oeuvre tous les moyens raisonnables pour assurer la fiabilite et la disponibilite du service. Cependant, l'utilisateur reconnait que les agents IA fournissent des suggestions qui doivent etre verifiees par un professionnel qualifie. DouCompta ne saurait etre tenu responsable des consequences de decisions prises sur la base de ces suggestions sans verification prealable.</p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-gray-900 mb-3">Article 7 - Tarification</h2>
            <p className="text-gray-600 leading-relaxed">Les tarifs en vigueur sont disponibles sur le site. DouCompta se reserve le droit de modifier ses tarifs, sous reserve d'un preavis de 30 jours. L'utilisateur peut resilier son abonnement a tout moment depuis son espace client.</p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-gray-900 mb-3">Article 8 - Resiliation</h2>
            <p className="text-gray-600 leading-relaxed">L'utilisateur peut resilier son compte a tout moment. En cas de resiliation, les donnees seront conservees pendant 10 ans conformement aux obligations legales de conservation des documents comptables (article L123-22 du Code de commerce).</p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-gray-900 mb-3">Article 9 - Droit applicable et juridiction</h2>
            <p className="text-gray-600 leading-relaxed">Les presentes CGU sont regies par le droit francais. Tout litige relatif a leur interpretation ou execution releve de la competence exclusive des tribunaux de Paris.</p>
          </section>
        </div>

        <div className="mt-12 pt-6 border-t border-gray-200">
          <p className="text-sm text-gray-400 mb-4">Version 1.0 - Mars 2026</p>
          <div className="flex flex-wrap gap-4 text-sm">
            <Link href="/legal/mentions-legales" className="text-indigo-600 hover:underline">Mentions legales</Link>
            <Link href="/legal/confidentialite" className="text-indigo-600 hover:underline">Confidentialite</Link>
            <Link href="/legal/cookies" className="text-indigo-600 hover:underline">Cookies</Link>
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
