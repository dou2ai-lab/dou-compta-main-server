'use client'

import Link from 'next/link'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { faArrowLeft, faReceipt } from '@fortawesome/free-solid-svg-icons'

export default function ConfidentialitePage() {
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
        <h1 className="text-3xl font-bold text-gray-900 mb-8">Politique de Confidentialite</h1>

        <div className="prose prose-gray max-w-none space-y-8">
          <section>
            <h2 className="text-xl font-semibold text-gray-900 mb-3">1. Responsable du traitement</h2>
            <p className="text-gray-600 leading-relaxed">DouCompta SAS, 12 Rue de la Paix, 75002 Paris. DPO : <a href="mailto:dpo@doucompta.fr" className="text-indigo-600 hover:underline">dpo@doucompta.fr</a></p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-gray-900 mb-3">2. Donnees collectees</h2>
            <ul className="text-gray-600 space-y-2 list-disc pl-5">
              <li><strong>Donnees d'identification</strong> : nom, prenom, email, telephone</li>
              <li><strong>Donnees professionnelles</strong> : SIREN, SIRET, forme juridique, regime fiscal</li>
              <li><strong>Donnees comptables</strong> : ecritures, factures, releves bancaires, declarations</li>
              <li><strong>Donnees de connexion</strong> : adresse IP, logs, cookies techniques</li>
            </ul>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-gray-900 mb-3">3. Finalites du traitement</h2>
            <ul className="text-gray-600 space-y-2 list-disc pl-5">
              <li>Fourniture du service de comptabilite automatisee</li>
              <li>Generation des ecritures comptables et declarations fiscales</li>
              <li>Analyse financiere et previsions de tresorerie</li>
              <li>Support client et amelioration du service</li>
              <li>Respect des obligations legales (conservation comptable, FEC)</li>
            </ul>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-gray-900 mb-3">4. Base legale</h2>
            <p className="text-gray-600 leading-relaxed">Le traitement est fonde sur : l'execution du contrat (article 6.1.b RGPD), le respect des obligations legales comptables et fiscales (article 6.1.c), et l'interet legitime de DouCompta pour l'amelioration du service (article 6.1.f).</p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-gray-900 mb-3">5. Hebergement et securite</h2>
            <p className="text-gray-600 leading-relaxed">Toutes les donnees sont hebergees en France chez OVHcloud (datacenters certifies ISO 27001, HDS). Les donnees sont chiffrees en transit (TLS 1.3) et au repos (AES-256). Aucun transfert de donnees hors de l'Union Europeenne.</p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-gray-900 mb-3">6. Duree de conservation</h2>
            <ul className="text-gray-600 space-y-2 list-disc pl-5">
              <li>Donnees comptables : 10 ans (obligation legale)</li>
              <li>Donnees de facturation : 10 ans</li>
              <li>Donnees de connexion : 1 an</li>
              <li>Donnees de compte : duree du contrat + 3 ans</li>
            </ul>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-gray-900 mb-3">7. Vos droits</h2>
            <p className="text-gray-600 leading-relaxed">Conformement au RGPD, vous disposez des droits suivants : acces, rectification, effacement, limitation, portabilite, opposition. Vous pouvez egalement definir des directives relatives au sort de vos donnees apres votre deces. Pour exercer vos droits : <a href="mailto:dpo@doucompta.fr" className="text-indigo-600 hover:underline">dpo@doucompta.fr</a></p>
            <p className="text-gray-600 leading-relaxed mt-2">En cas de reclamation, vous pouvez saisir la CNIL : <a href="https://www.cnil.fr" className="text-indigo-600 hover:underline" target="_blank" rel="noopener noreferrer">www.cnil.fr</a></p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-gray-900 mb-3">8. Intelligence artificielle</h2>
            <p className="text-gray-600 leading-relaxed">DouCompta utilise des agents IA pour automatiser les taches comptables. Aucune decision automatisee n'est prise sans possibilite de verification humaine. Les modeles IA sont entraines exclusivement sur des donnees anonymisees et ne sont pas utilises a des fins de profilage.</p>
          </section>
        </div>

        <div className="mt-12 pt-6 border-t border-gray-200">
          <p className="text-sm text-gray-400 mb-4">Derniere mise a jour : Mars 2026</p>
          <div className="flex flex-wrap gap-4 text-sm">
            <Link href="/legal/mentions-legales" className="text-indigo-600 hover:underline">Mentions legales</Link>
            <Link href="/legal/cgu" className="text-indigo-600 hover:underline">CGU</Link>
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
