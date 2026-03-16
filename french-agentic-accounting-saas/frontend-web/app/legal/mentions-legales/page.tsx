'use client'

import Link from 'next/link'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { faArrowLeft, faReceipt } from '@fortawesome/free-solid-svg-icons'

export default function MentionsLegalesPage() {
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
        <h1 className="text-3xl font-bold text-gray-900 mb-8">Mentions Legales</h1>

        <div className="prose prose-gray max-w-none space-y-8">
          <section>
            <h2 className="text-xl font-semibold text-gray-900 mb-3">1. Editeur du site</h2>
            <p className="text-gray-600 leading-relaxed">
              <strong>DouCompta SAS</strong><br />
              Societe par Actions Simplifiee au capital de 100 000 EUR<br />
              Siege social : 12 Rue de la Paix, 75002 Paris, France<br />
              SIREN : 912 345 678<br />
              RCS Paris B 912 345 678<br />
              N° TVA intracommunautaire : FR 12 912345678<br />
              Directeur de la publication : M. Antoine Moreau, President
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-gray-900 mb-3">2. Hebergement</h2>
            <p className="text-gray-600 leading-relaxed">
              Le site est heberge en France par :<br />
              <strong>OVHcloud</strong><br />
              2 Rue Kellermann, 59100 Roubaix, France<br />
              SAS au capital de 10 174 560 EUR<br />
              RCS Lille Metropole 424 761 419<br />
              Telephone : +33 9 72 10 10 07<br />
              Les donnees sont exclusivement stockees sur le territoire francais, conformement aux exigences de souverainete numerique.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-gray-900 mb-3">3. Contact</h2>
            <p className="text-gray-600 leading-relaxed">
              Email : <a href="mailto:contact@doucompta.fr" className="text-indigo-600 hover:underline">contact@doucompta.fr</a><br />
              Telephone : +33 1 42 00 00 00<br />
              Formulaire de contact : <Link href="/contact" className="text-indigo-600 hover:underline">www.doucompta.fr/contact</Link>
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-gray-900 mb-3">4. Propriete intellectuelle</h2>
            <p className="text-gray-600 leading-relaxed">
              L'ensemble du contenu du site DouCompta (textes, graphismes, images, logos, icones, logiciels, bases de donnees) est protege par les lois francaises et internationales relatives a la propriete intellectuelle. Toute reproduction, representation, modification, publication, transmission ou denaturation, totale ou partielle, du site ou de son contenu, par quelque procede que ce soit, et sur quelque support que ce soit, est interdite sans l'autorisation ecrite prealable de DouCompta SAS.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-gray-900 mb-3">5. Donnees personnelles</h2>
            <p className="text-gray-600 leading-relaxed">
              Conformement au Reglement General sur la Protection des Donnees (RGPD) et a la loi Informatique et Libertes du 6 janvier 1978 modifiee, vous disposez d'un droit d'acces, de rectification, de suppression, de limitation, de portabilite et d'opposition au traitement de vos donnees personnelles. Pour exercer ces droits, contactez notre Delegue a la Protection des Donnees (DPO) : <a href="mailto:dpo@doucompta.fr" className="text-indigo-600 hover:underline">dpo@doucompta.fr</a>
            </p>
            <p className="text-gray-600 leading-relaxed mt-2">
              Pour plus d'informations, consultez notre <Link href="/legal/confidentialite" className="text-indigo-600 hover:underline">Politique de Confidentialite</Link>.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-gray-900 mb-3">6. Cookies</h2>
            <p className="text-gray-600 leading-relaxed">
              Le site utilise des cookies strictement necessaires au fonctionnement du service. Aucun cookie de tracking ou publicitaire n'est utilise. Pour plus d'informations, consultez notre <Link href="/legal/cookies" className="text-indigo-600 hover:underline">Politique de Cookies</Link>.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-gray-900 mb-3">7. Droit applicable</h2>
            <p className="text-gray-600 leading-relaxed">
              Les presentes mentions legales sont soumises au droit francais. En cas de litige, et apres tentative de resolution amiable, les tribunaux de Paris seront seuls competents.
            </p>
          </section>
        </div>

        <div className="mt-12 pt-6 border-t border-gray-200">
          <p className="text-sm text-gray-400 mb-4">Derniere mise a jour : Mars 2026</p>
          <div className="flex flex-wrap gap-4 text-sm">
            <Link href="/legal/cgu" className="text-indigo-600 hover:underline">CGU</Link>
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
