'use client'

import React, { createContext, useContext, useState, useCallback, useEffect, useRef } from 'react'

export type Locale = 'en' | 'fr'

/** Call Next.js API route that proxies to LibreTranslate */
async function translateWithAPI(text: string, target: Locale): Promise<string> {
  if (!text.trim()) return text
  if (target === 'en') return text
  const res = await fetch('/api/translate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text: text.trim(), target }),
  })
  const data = await res.json()
  if (!res.ok) return text
  return data?.translatedText ?? text
}

const STORAGE_KEY = 'app-locale'

const translations: Record<Locale, Record<string, unknown>> = {
  en: {
    common: {
      home: 'Home',
      dashboard: 'Dashboard',
      view: 'View', edit: 'Edit', delete: 'Delete', loading: 'Loading', export: 'Export',
      submitReport: 'Submit Report', newExpense: 'New Expense', vsLastMonth: 'vs last month',
      requiresYourAction: 'Requires your action', vsBudget: 'vs budget', date: 'Date', merchant: 'Merchant',
      category: 'Category', amount: 'Amount', status: 'Status', actions: 'Actions', pending: 'pending',
      thisMonthTotal: 'This month total', other: 'Other',
    },
    header: {
      searchPlaceholder: 'Search expenses, reports, invoices...',
      language: 'Language',
      french: 'French',
      english: 'English',
      logout: 'Log out',
    },
    sidebar: {
      dashboard: 'Dashboard',
      expenses: 'Expenses',
      reports: 'Reports',
      approvals: 'Approvals',
      jobs: 'Jobs',
      financeAudit: 'Finance & Audit',
      financeDashboard: 'Finance Dashboard',
      anomalies: 'Anomalies',
      auditReports: 'Audit Reports',
      auditCoPilot: 'Audit Co-Pilot',
      administration: 'Administration',
      usersRoles: 'Users & Roles',
      policies: 'Policies',
      categoriesGL: 'Categories & GL',
      integrations: 'Integrations',
      settings: 'Settings',
      financeManager: 'Finance Manager',
      accounting: 'Accounting',
      dossiers: 'Client Dossiers',
      banking: 'Banking',
      tax: 'Tax',
      analysis: 'Analysis',
      invoices: 'Invoices',
      payroll: 'Payroll',
      documents: 'Documents',
      agents: 'Agents',
    },
    routes: {
      admin: 'Administration',
      dashboard: 'Dashboard',
      expenses: 'Expenses',
      reports: 'Reports',
      approvals: 'Approvals',
      jobs: 'Jobs',
      finance: 'Finance',
      anomalies: 'Anomalies',
      audit: 'Audit',
      users: 'Users',
      categories: 'Categories',
      integrations: 'Integrations',
      settings: 'Settings',
      'audit-reports': 'Audit Reports',
      'audit-copilot': 'Audit Co-Pilot',
      'evidence-pack': 'Evidence Pack',
      notifications: 'Notifications',
    },
    statusLabel: {
      draft: 'Draft', approved: 'Approved', rejected: 'Rejected', submitted: 'Submitted', pending: 'Pending',
    },
    policies: {
      title: 'Policy Builder',
      subtitle: 'Configure expense policies and compliance rules',
      export: 'Export',
      import: 'Import',
      createPolicy: 'Create Policy',
      frenchTemplates: 'French Compliance Templates',
      frenchTemplatesDesc: 'Pre-configured policies for French regulations',
      viewAllTemplates: 'View All Templates',
      activePolicies: 'Active Policies',
      searchPolicies: 'Search policies...',
      policyEditor: 'Policy Editor',
      policyEditorDesc: 'Configure policy details and rules',
      selectPolicyToEdit: 'Select a policy from the list to edit or create one',
      active: 'Active',
      activePoliciesCount: 'Active Policies',
      draft: 'Draft',
      draftPolicies: 'Draft Policies',
      awaitingActivation: 'Awaiting activation',
      compliantExpenses: 'Compliant Expenses',
      thisMonth: 'This month',
      policyViolations: 'Policy Violations',
      requiresReview: 'Requires review',
      impactAnalysis: 'Policy Impact Analysis',
      impactAnalysisDesc: 'How policies affect expense submissions',
      autoApproved: 'Auto-Approved',
      expensesPassedChecks: 'Expenses passed all checks',
      flaggedForReview: 'Flagged for Review',
      requiredManualApproval: 'Required manual approval',
      blockedRejected: 'Blocked/Rejected',
      violationsDetected: 'Policy violations detected',
      recentViolations: 'Recent Policy Violations',
      recentViolationsDesc: 'Expenses that triggered policy alerts',
      viewAllViolations: 'View All Violations',
      employee: 'Employee',
      policy: 'Policy',
      violation: 'Violation',
      severity: 'Severity',
      review: 'Review',
      confirmDelete: 'Delete this policy?',
      basicInfo: 'Basic Information',
      policyName: 'Policy Name',
      policyType: 'Policy Type',
      description: 'Description',
      describePolicy: 'Describe this policy...',
      ruleBuilder: 'Rule Configuration',
      addRule: 'Add Rule',
      primaryRule: 'Primary Rule',
      exceptionRule: 'Exception Rule',
      conditionsAllTrue: 'Conditions (All must be true)',
      actions: 'Actions',
      addCondition: 'Add Condition (AND)',
      addAction: 'Add Action',
      messageOrDetails: 'Message or details...',
      effectiveDates: 'Effective Dates',
      startDate: 'Start Date',
      endDate: 'End Date',
      noEndDate: 'No end date',
      noEndDateHint: 'Leave empty for no expiration',
      saveDraft: 'Save as Draft',
      saveActivate: 'Save & Activate',
      testPolicy: 'Test Policy',
      testPolicyDesc: 'Preview how this policy works with sample data',
      runTest: 'Run Test',
      sampleInput: 'Sample Input',
      expectedResult: 'Expected Result',
      expenseAllowed: 'Expense Allowed',
      withinLimit: 'Amount is within meal allowance limit',
      ruleApplied: 'Rule Applied',
      complianceStatus: 'Compliance Status',
      urssafCompliant: 'URSSAF compliant - within daily limit',
      categoryScope: 'Category Scope',
      entityScope: 'Entity Scope',
      roleScope: 'Role Scope',
      locationScope: 'Location Scope',
      noViolations: 'No recent policy violations. Expenses that trigger policy alerts will appear here.',
      howDataGenerated: 'How this data is generated:',
      howDataGeneratedDesc: 'Active and draft counts come from the policies above. Compliant expenses, policy violations, and the table below are filled when users submit expenses that are then evaluated against these policies.',
      goToExpenses: 'Submit expenses via Expenses',
      howDataGeneratedSuffix: ' to see stats and violations update.',
      submitTip: 'Use "Submit for Approval" (not Save as Draft) and set Category so policies (e.g. meal/hotel) can run.',
    },
    categories: {
      title: 'Categories & GL',
      subtitle: 'Manage expense categories and general ledger mappings',
      newCategory: 'New Category',
      totalCategories: 'Total Categories',
      glAccounts: 'GL Accounts',
      activeCategories: 'Active Categories',
      categoryTree: 'Category Tree',
      searchCategories: 'Search categories...',
      selectCategory: 'Select a category from the tree or create a new one',
      saveChanges: 'Save Changes',
      parentCategory: 'Parent Category',
      noneRoot: 'None (Root Level)',
      glMapping: 'GL Account Mapping',
      addSubcategory: 'Add subcategory',
      deleteCategory: 'Delete Category',
      glIntegration: 'GL Account Integration',
      glIntegrationDesc: 'General ledger accounts available for category mapping',
      searchGL: 'Search GL accounts...',
      accountCode: 'Account Code',
      accountName: 'Account Name',
      accountType: 'Account Type',
      mappedCategories: 'Mapped Categories',
      showingGL: 'Showing',
    },
    dashboard: {
      goodMorning: 'Good morning, Jean', pendingExpenses: 'Pending Expenses', awaitingApproval: 'Awaiting Approval',
      thisMonthSpend: 'This Month Spend', vatRecoverable: 'VAT Recoverable', recentExpenses: 'Recent Expenses',
      yourLatestExpenses: 'Your latest expense submissions', viewAllExpenses: 'View All Expenses',
      expenseTrends: 'Expense Trends', monthlySpendAnalysis: 'Monthly spending analysis', months6: '6 Months',
      year1: '1 Year', quickSubmit: 'Quick Submit', uploadReceiptAi: 'Upload receipt and AI will handle the rest',
      dragDropReceipt: 'Drag & drop receipt here', orClickToBrowse: 'or click to browse', takePhoto: 'Take Photo',
      emailReceipt: 'Email Receipt', pendingApprovals: 'Pending Approvals', expensesAwaitingReview: 'Expenses awaiting your review',
      viewAllPending: 'View All Pending (5)', aiInsights: 'AI Insights', proactiveSuggestions: 'Proactive suggestions & alerts',
      receiptsAwaitingCategorization: 'Receipts Awaiting Categorization', youHaveReceiptsToCategorize: 'You have 3 receipts that need to be categorized and submitted',
      reviewNow: 'Review Now →', unusualActivityDetected: 'Unusual Activity Detected', unusualSpendingPattern: 'Unusual spending pattern detected for "Uber Paris" - 5 trips in one day',
      investigate: 'Investigate →', optimizationSuggestion: 'Optimization Suggestion', savePercentByBooking: 'Save 15% by booking train tickets 2 weeks in advance instead of last minute',
      learnMore: 'Learn More →', loadingRecentExpenses: 'Loading recent expenses...', noExpensesYet: 'No expenses yet. Create your first expense to get started.',
      overdue: 'Overdue', accommodation: 'Accommodation', meals: 'Meals', transport: 'Transport',
      travel: 'Travel', office: 'Office', training: 'Training',
      marketingTeam: 'Marketing Team', salesDepartment: 'Sales Department', operationsTeam: 'Operations Team',
      dayAgo: '1 day ago', hoursAgo: '5 hours ago', alert: 'Alert', tip: 'Tip',
    },
    login: {
      platformTagline: 'Expense & Audit AI Platform', title: 'AI-Powered Expense Management',
      subtitle: 'Automate, audit, and optimize your company expenses with intelligent compliance.',
      feature1Title: 'AI-Powered Receipt Scanning', feature1Desc: 'Automatic OCR extraction with 98% accuracy for French receipts',
      feature2Title: 'URSSAF & VAT Compliance', feature2Desc: 'Automatic compliance checks for French regulations and tax laws',
      feature3Title: 'Real-Time Anomaly Detection', feature3Desc: 'AI audit co-pilot identifies risks and policy violations instantly',
      testimonialRole: 'Finance Director, TechCorp', testimonialQuote: '"Dou reduced our expense processing time by 75% and improved compliance to 99.5%. The AI audit features are game-changing."',
      welcome: 'Welcome', signInToAccount: 'Sign in to your Dou account', continueWithMicrosoft: 'Continue with Microsoft',
      continueWithGoogle: 'Continue with Google', continueWithOkta: 'Continue with Okta', orContinueWithEmail: 'or continue with email',
      email: 'Email', emailPlaceholder: 'you@company.com', emailError: 'Please enter a valid email address',
      password: 'Password', passwordPlaceholder: '••••••••', passwordError: 'Password is required',
      rememberMe: 'Stay signed in', forgotPassword: 'Forgot password?', signIn: 'Sign in', signingIn: 'Signing in...',
      sessionExpired: 'Session expired', sessionExpiredDesc: 'Your session has expired. Please sign in again.',
      loginError: 'Login error', loginErrorDesc: 'Invalid email or password. Please try again.',
      redirecting: 'Redirecting...', redirectingDesc: 'You are being redirected to', noAccount: "Don't have an account?", createAccount: 'Create an account',
      termsOfUse: 'Terms of use', privacyPolicy: 'Privacy policy', support: 'Support', copyright: '© 2025 Dou. All rights reserved.',
    },
    signup: {
      platformTagline: 'Expense & Audit AI Platform',
      title: 'Join the Dou experience',
      subtitle: 'Create your account to automate expense reports and secure URSSAF & VAT compliance.',
      feature1Title: 'Smart receipt scanning',
      feature1Desc: 'Automatic extraction with 98% accuracy on French receipts.',
      feature2Title: 'URSSAF & VAT compliance',
      feature2Desc: 'Automatic compliance checks for French rules and recoverable VAT.',
      feature3Title: 'Audit and anomaly detection',
      feature3Desc: 'AI identifies risks, potential fraud, and policy violations instantly.',
      testimonialRole: 'Finance Director, TechCorp',
      testimonialQuote: '"We rolled out Dou across the company in weeks. Expense management has never been simpler."',
      welcome: 'Create your account',
      signUpToStart: 'Sign up to get started with Dou',
      continueWithMicrosoft: 'Continue with Microsoft',
      continueWithGoogle: 'Continue with Google',
      orContinueWithEmail: 'or create an account with your email',
      firstName: 'First name (optional)',
      lastName: 'Last name (optional)',
      firstNamePlaceholder: 'Jean',
      lastNamePlaceholder: 'Dupont',
      email: 'Work email',
      emailPlaceholder: 'you@company.com',
      emailError: 'Please enter a valid email address',
      password: 'Password (min. 8 characters)',
      passwordPlaceholder: '••••••••',
      passwordError: 'Password must be at least 8 characters',
      confirmPassword: 'Confirm password',
      confirmPasswordError: 'Passwords do not match',
      createAccount: 'Create account',
      creatingAccount: 'Creating account...',
      alreadyHaveAccount: 'Already have an account?',
      signIn: 'Sign in',
      createAccountError: 'Account creation failed. Please try again.',
      redirecting: 'Redirecting...',
      redirectingDesc: 'You are being redirected to',
    },
    expenses: {
      myExpenses: 'My Expenses', manageAndTrack: 'Manage and track all your expense submissions',
      totalExpenses: 'Total Expenses', totalAmount: 'Total Amount', searchPlaceholder: 'Search expenses...',
      filters: 'Filters', sort: 'Sort', description: 'Description', vat: 'VAT',
      noExpensesMatch: 'No expenses match your filters.', newExpenseToGetStarted: 'Create your first expense to get started.',
    },
    reports: {
      title: 'Expense Reports', subtitle: 'View and manage all your expense reports',
      newReport: 'New Report', filter: 'Filter', all: 'All', approved: 'Approved', submitted: 'Submitted', draft: 'Draft',
      monthlyReport: 'Monthly Report', tripReport: 'Trip-based Report', viewReport: 'View Report', createdBy: 'Created by',
      allReports: 'All Reports', searchPlaceholder: 'Search reports...', reports: 'Reports', manageTrack: 'Manage and track all expense reports',
      expensesCount: 'expenses', total: 'Total',
    },
    settings: {
      title: 'Company Settings', subtitle: 'Configure company-wide settings, compliance rules, and system preferences',
      saveChanges: 'Save Changes', viewChangeLog: 'View Change Log',
      general: 'General', usersPermissions: 'Users & Permissions', security: 'Security', notifications: 'Notifications', billing: 'Billing',
      settings: 'Settings', configurePreferences: 'Configure preferences', companyName: 'Company Name', companyAddress: 'Company Address',
    },
    approvals: {
      title: 'Approvals', subtitle: 'Review and approve expense submissions',
      pendingApprovals: 'Pending Approvals', filter: 'Filter', sortBy: 'Sort By', bulkApprove: 'Bulk Approve',
      all: 'All', myQueue: 'My Queue', escalated: 'Escalated', completed: 'Completed',
      approve: 'Approve', reject: 'Reject', viewDetails: 'View Details', risk: 'Risk', high: 'High', medium: 'Medium', low: 'Low',
      items: 'Items', department: 'Department', submittedDate: 'Submitted', issues: 'Issues', allCompliant: 'All compliant',
      highRiskDetected: 'High Risk Detected', highRiskDesc: 'AI has identified 2 policy violations that require your attention before approval.',
      viewDetailsLink: 'View Details →', expenseItems: 'Expense Items', viewAll: 'View All', policyViolations: 'Policy Violations',
      requestInfo: 'Request Info', submittedOn: 'Submitted on', riskLabel: 'Risk',
    },
  },
  fr: {
    common: {
      home: 'Accueil',
      dashboard: 'Tableau de bord',
      view: 'Voir', edit: 'Modifier', delete: 'Supprimer', loading: 'Chargement', export: 'Exporter',
      submitReport: 'Soumettre un rapport', newExpense: 'Nouvelle dépense', vsLastMonth: 'vs mois dernier',
      requiresYourAction: 'Nécessite votre action', vsBudget: 'vs budget', date: 'Date', merchant: 'Fournisseur',
      category: 'Catégorie', amount: 'Montant', status: 'Statut', actions: 'Actions', pending: 'en attente',
      thisMonthTotal: 'Total ce mois', other: 'Autre',
    },
    header: {
      searchPlaceholder: 'Rechercher dépenses, rapports, factures...',
      language: 'Langue',
      french: 'Français',
      english: 'Anglais',
      logout: 'Déconnexion',
    },
    sidebar: {
      dashboard: 'Tableau de bord',
      expenses: 'Dépenses',
      reports: 'Rapports',
      approvals: 'Approbations',
      jobs: 'Emplois',
      financeAudit: 'Finance & Audit',
      financeDashboard: 'Tableau de bord finance',
      anomalies: 'Anomalies',
      auditReports: 'Rapports d\'audit',
      auditCoPilot: 'Audit Co-Pilot',
      administration: 'Administration',
      usersRoles: 'Utilisateurs & Rôles',
      policies: 'Politiques',
      categoriesGL: 'Catégories & Comptabilité',
      integrations: 'Intégrations',
      settings: 'Paramètres',
      financeManager: 'Responsable financier',
      accounting: 'Comptabilité',
      dossiers: 'Dossiers Clients',
      banking: 'Banque',
      tax: 'Fiscalité',
      analysis: 'Analyse',
      invoices: 'Factures',
      payroll: 'Paie',
      documents: 'Documents',
      agents: 'Agents',
    },
    routes: {
      admin: 'Administration',
      dashboard: 'Tableau de bord',
      expenses: 'Dépenses',
      reports: 'Rapports',
      approvals: 'Approbations',
      jobs: 'Emplois',
      finance: 'Finance',
      anomalies: 'Anomalies',
      audit: 'Audit',
      users: 'Utilisateurs',
      categories: 'Catégories',
      integrations: 'Intégrations',
      settings: 'Paramètres',
      'audit-reports': 'Rapports d\'audit',
      'audit-copilot': 'Audit Co-Pilot',
      'evidence-pack': 'Dossier de preuves',
      notifications: 'Notifications',
    },
    statusLabel: {
      draft: 'Brouillon', approved: 'Approuvé', rejected: 'Refusé', submitted: 'Soumis', pending: 'En attente',
    },
    policies: {
      title: 'Gestion des politiques',
      subtitle: 'Configurer les politiques de dépenses et les règles de conformité',
      export: 'Exporter',
      import: 'Importer',
      createPolicy: 'Créer une politique',
      frenchTemplates: 'Modèles de conformité France',
      frenchTemplatesDesc: 'Politiques préconfigurées pour la réglementation française',
      viewAllTemplates: 'Voir tous les modèles',
      activePolicies: 'Politiques actives',
      searchPolicies: 'Rechercher des politiques...',
      policyEditor: 'Éditeur de politique',
      policyEditorDesc: 'Configurer les détails et les règles',
      selectPolicyToEdit: 'Sélectionnez une politique dans la liste pour la modifier ou en créer une',
      active: 'Active',
      activePoliciesCount: 'Politiques actives',
      draft: 'Brouillon',
      draftPolicies: 'Politiques brouillon',
      awaitingActivation: 'En attente d\'activation',
      compliantExpenses: 'Dépenses conformes',
      thisMonth: 'Ce mois',
      policyViolations: 'Violations de politique',
      requiresReview: 'À examiner',
      impactAnalysis: 'Impact des politiques',
      impactAnalysisDesc: 'Comment les politiques affectent les dépenses',
      autoApproved: 'Approuvées automatiquement',
      expensesPassedChecks: 'Dépenses conformes',
      flaggedForReview: 'À revoir',
      requiredManualApproval: 'Approbation manuelle requise',
      blockedRejected: 'Bloquées / Refusées',
      violationsDetected: 'Violations détectées',
      recentViolations: 'Violations récentes',
      recentViolationsDesc: 'Dépenses ayant déclenché une alerte',
      viewAllViolations: 'Voir toutes les violations',
      employee: 'Employé',
      policy: 'Politique',
      violation: 'Violation',
      severity: 'Gravité',
      review: 'Examiner',
      confirmDelete: 'Supprimer cette politique ?',
      basicInfo: 'Informations générales',
      policyName: 'Nom de la politique',
      policyType: 'Type de politique',
      description: 'Description',
      describePolicy: 'Décrivez cette politique...',
      ruleBuilder: 'Configuration des règles',
      addRule: 'Ajouter une règle',
      primaryRule: 'Règle principale',
      exceptionRule: 'Règle d\'exception',
      conditionsAllTrue: 'Conditions (toutes doivent être vraies)',
      actions: 'Actions',
      addCondition: 'Ajouter une condition (ET)',
      addAction: 'Ajouter une action',
      messageOrDetails: 'Message ou détails...',
      effectiveDates: 'Dates d\'effet',
      startDate: 'Date de début',
      endDate: 'Date de fin',
      noEndDate: 'Sans date de fin',
      noEndDateHint: 'Laisser vide pour aucune expiration',
      saveDraft: 'Enregistrer en brouillon',
      saveActivate: 'Enregistrer et activer',
      testPolicy: 'Tester la politique',
      testPolicyDesc: 'Aperçu du comportement avec des données de test',
      runTest: 'Lancer le test',
      sampleInput: 'Données de test',
      expectedResult: 'Résultat attendu',
      expenseAllowed: 'Dépense autorisée',
      withinLimit: 'Montant dans la limite',
      ruleApplied: 'Règle appliquée',
      complianceStatus: 'Conformité',
      urssafCompliant: 'Conforme URSSAF - dans la limite journalière',
      categoryScope: 'Catégories concernées',
      entityScope: 'Entités concernées',
      roleScope: 'Rôles concernés',
      locationScope: 'Zones géographiques',
      noViolations: 'Aucune violation de politique récente. Les dépenses déclenchant une alerte apparaîtront ici.',
      howDataGenerated: 'Comment ces données sont générées :',
      howDataGeneratedDesc: 'Les comptes Actives et Brouillons viennent des politiques ci-dessus. Les dépenses conformes, les violations et le tableau ci-dessous se remplissent lorsque des utilisateurs soumettent des dépenses évaluées par ces politiques.',
      goToExpenses: 'Soumettre des dépenses via Dépenses',
      howDataGeneratedSuffix: ' pour voir les statistiques et les violations se mettre à jour.',
      submitTip: 'Utilisez « Soumettre pour approbation » (pas « Enregistrer comme brouillon ») et renseignez la catégorie pour que les politiques (repas, hôtel, etc.) s\'appliquent.',
    },
    categories: {
      title: 'Catégories & Comptabilité',
      subtitle: 'Gérer les catégories de dépense et les mappings comptables',
      newCategory: 'Nouvelle catégorie',
      totalCategories: 'Total des catégories',
      glAccounts: 'Comptes comptables',
      activeCategories: 'Catégories actives',
      categoryTree: 'Arborescence des catégories',
      searchCategories: 'Rechercher des catégories...',
      selectCategory: 'Sélectionnez une catégorie dans l’arborescence ou créez-en une',
      saveChanges: 'Enregistrer',
      parentCategory: 'Catégorie parente',
      noneRoot: 'Aucune (niveau racine)',
      glMapping: 'Mapping compte comptable',
      addSubcategory: 'Ajouter une sous-catégorie',
      deleteCategory: 'Supprimer la catégorie',
      glIntegration: 'Intégration comptes comptables',
      glIntegrationDesc: 'Comptes comptables disponibles pour le mapping des catégories',
      searchGL: 'Rechercher des comptes...',
      accountCode: 'Code compte',
      accountName: 'Nom du compte',
      accountType: 'Type',
      mappedCategories: 'Catégories mappées',
      showingGL: 'Affichage',
    },
    dashboard: {
      goodMorning: 'Bonjour, Jean', pendingExpenses: 'Dépenses en attente', awaitingApproval: 'En attente d\'approbation',
      thisMonthSpend: 'Dépenses du mois', vatRecoverable: 'TVA récupérable', recentExpenses: 'Dépenses récentes',
      yourLatestExpenses: 'Vos dernières dépenses soumises', viewAllExpenses: 'Voir toutes les dépenses',
      expenseTrends: 'Évolution des dépenses', monthlySpendAnalysis: 'Analyse des dépenses mensuelles', months6: '6 mois',
      year1: '1 an', quickSubmit: 'Soumission rapide', uploadReceiptAi: 'Téléchargez un reçu, l\'IA s\'occupe du reste',
      dragDropReceipt: 'Glissez-déposez un reçu ici', orClickToBrowse: 'ou cliquez pour parcourir', takePhoto: 'Prendre une photo',
      emailReceipt: 'Envoyer par email', pendingApprovals: 'Approbations en attente', expensesAwaitingReview: 'Dépenses en attente de votre revue',
      viewAllPending: 'Voir tout (5)', aiInsights: 'Conseils IA', proactiveSuggestions: 'Suggestions et alertes proactives',
      receiptsAwaitingCategorization: 'Reçus à catégoriser', youHaveReceiptsToCategorize: 'Vous avez 3 reçus à catégoriser et soumettre',
      reviewNow: 'Réviser maintenant →', unusualActivityDetected: 'Activité inhabituelle détectée', unusualSpendingPattern: 'Dépenses inhabituelles pour « Uber Paris » - 5 trajets en un jour',
      investigate: 'Examiner →', optimizationSuggestion: 'Suggestion d\'optimisation', savePercentByBooking: 'Économisez 15 % en réservant vos billets de train 2 semaines à l\'avance',
      learnMore: 'En savoir plus →', loadingRecentExpenses: 'Chargement des dépenses...', noExpensesYet: 'Aucune dépense. Créez votre première dépense pour commencer.',
      overdue: 'En retard', accommodation: 'Hébergement', meals: 'Repas', transport: 'Transport',
      travel: 'Voyage', office: 'Bureau', training: 'Formation',
      marketingTeam: 'Équipe marketing', salesDepartment: 'Service commercial', operationsTeam: 'Équipe opérations',
      dayAgo: 'Il y a 1 jour', hoursAgo: 'Il y a 5 h', alert: 'Alerte', tip: 'Conseil',
    },
    login: {
      platformTagline: 'Plateforme Dépenses & Audit IA', title: 'Gestion des dépenses par l\'IA',
      subtitle: 'Automatisez, auditez et optimisez les dépenses de votre entreprise avec une conformité intelligente.',
      feature1Title: 'Numérisation des reçus par IA', feature1Desc: 'Extraction OCR automatique avec 98 % de précision pour les reçus français',
      feature2Title: 'Conformité URSSAF & TVA', feature2Desc: 'Contrôles automatiques des réglementations et lois fiscales françaises',
      feature3Title: 'Détection d\'anomalies en temps réel', feature3Desc: 'L\'assistant d\'audit IA identifie les risques et les violations instantanément',
      testimonialRole: 'Directeur financier, TechCorp', testimonialQuote: '« Dou a réduit notre temps de traitement des dépenses de 75 % et porté la conformité à 99,5 %. Les fonctionnalités d\'audit IA changent la donne. »',
      welcome: 'Bienvenue', signInToAccount: 'Connectez-vous à votre compte Dou', continueWithMicrosoft: 'Continuer avec Microsoft',
      continueWithGoogle: 'Continuer avec Google', continueWithOkta: 'Continuer avec Okta', orContinueWithEmail: 'ou continuer avec l\'email',
      email: 'Email', emailPlaceholder: 'vous@entreprise.com', emailError: 'Veuillez entrer une adresse email valide',
      password: 'Mot de passe', passwordPlaceholder: '••••••••', passwordError: 'Le mot de passe est requis',
      rememberMe: 'Rester connecté', forgotPassword: 'Mot de passe oublié ?', signIn: 'Se connecter', signingIn: 'Connexion...',
      sessionExpired: 'Session expirée', sessionExpiredDesc: 'Votre session a expiré. Veuillez vous reconnecter.',
      loginError: 'Erreur de connexion', loginErrorDesc: 'Email ou mot de passe incorrect. Veuillez réessayer.',
      redirecting: 'Redirection en cours...', redirectingDesc: 'Vous allez être redirigé vers', noAccount: 'Pas encore de compte ?', createAccount: 'Créer un compte',
      termsOfUse: 'Conditions d\'utilisation', privacyPolicy: 'Politique de confidentialité', support: 'Support', copyright: '© 2025 Dou. Tous droits réservés.',
    },
    signup: {
      platformTagline: 'Plateforme Dépenses & Audit IA',
      title: 'Rejoignez l\'expérience Dou',
      subtitle: 'Créez votre compte pour automatiser vos notes de frais et sécuriser votre conformité URSSAF & TVA.',
      feature1Title: 'Scan intelligent des reçus',
      feature1Desc: 'Extraction automatique avec une précision de 98% sur les reçus français.',
      feature2Title: 'Conformité URSSAF & TVA',
      feature2Desc: 'Vérifications automatiques de conformité pour les règles françaises et la TVA récupérable.',
      feature3Title: 'Audit et détection d\'anomalies',
      feature3Desc: 'L\'IA identifie instantanément les risques, fraudes potentielles et violations de politiques.',
      testimonialRole: 'Directeur financier, TechCorp',
      testimonialQuote: '« Nous avons généralisé Dou à toute l\'entreprise en quelques semaines. La gestion des notes de frais n\'a jamais été aussi simple. »',
      welcome: 'Créer votre compte',
      signUpToStart: 'Inscrivez-vous pour démarrer avec Dou',
      continueWithMicrosoft: 'Continuer avec Microsoft',
      continueWithGoogle: 'Continuer avec Google',
      orContinueWithEmail: 'ou créer un compte avec votre email',
      firstName: 'Prénom (optionnel)',
      lastName: 'Nom (optionnel)',
      firstNamePlaceholder: 'Jean',
      lastNamePlaceholder: 'Dupont',
      email: 'Email professionnel',
      emailPlaceholder: 'vous@entreprise.com',
      emailError: 'Veuillez entrer une adresse email valide',
      password: 'Mot de passe (min. 8 caractères)',
      passwordPlaceholder: '••••••••',
      passwordError: 'Le mot de passe doit contenir au moins 8 caractères',
      confirmPassword: 'Confirmez le mot de passe',
      confirmPasswordError: 'Les mots de passe ne correspondent pas',
      createAccount: 'Créer le compte',
      creatingAccount: 'Création en cours...',
      alreadyHaveAccount: 'Déjà un compte ?',
      signIn: 'Se connecter',
      createAccountError: 'La création du compte a échoué. Veuillez réessayer.',
      redirecting: 'Redirection en cours...',
      redirectingDesc: 'Vous allez être redirigé vers',
    },
    expenses: {
      myExpenses: 'Mes dépenses', manageAndTrack: 'Gérez et suivez toutes vos dépenses',
      totalExpenses: 'Total des dépenses', totalAmount: 'Montant total', searchPlaceholder: 'Rechercher des dépenses...',
      filters: 'Filtres', sort: 'Trier', description: 'Description', vat: 'TVA',
      noExpensesMatch: 'Aucune dépense ne correspond à vos filtres.', newExpenseToGetStarted: 'Créez votre première dépense pour commencer.',
    },
    reports: {
      title: 'Rapports de dépenses', subtitle: 'Consulter et gérer tous vos rapports de dépenses',
      newReport: 'Nouveau rapport', filter: 'Filtrer', all: 'Tous', approved: 'Approuvé', submitted: 'Soumis', draft: 'Brouillon',
      monthlyReport: 'Rapport mensuel', tripReport: 'Rapport de déplacement', viewReport: 'Voir le rapport', createdBy: 'Créé par',
      allReports: 'Tous les rapports', searchPlaceholder: 'Rechercher des rapports...', reports: 'Rapports', manageTrack: 'Gérer et suivre tous les rapports de dépenses',
      expensesCount: 'dépenses', total: 'Total',
    },
    settings: {
      title: 'Paramètres de l\'entreprise', subtitle: 'Configurer les paramètres, règles de conformité et préférences',
      saveChanges: 'Enregistrer', viewChangeLog: 'Voir l\'historique',
      general: 'Général', usersPermissions: 'Utilisateurs et autorisations', security: 'Sécurité', notifications: 'Notifications', billing: 'Facturation',
      settings: 'Paramètres', configurePreferences: 'Configurer les préférences', companyName: 'Nom de l\'entreprise', companyAddress: 'Adresse',
    },
    approvals: {
      title: 'Approbations', subtitle: 'Réviser et approuver les dépenses',
      pendingApprovals: 'Approbations en attente', filter: 'Filtrer', sortBy: 'Trier par', bulkApprove: 'Approuver en masse',
      all: 'Tous', myQueue: 'Ma file', escalated: 'Escaladé', completed: 'Terminé',
      approve: 'Approuver', reject: 'Refuser', viewDetails: 'Voir le détail', risk: 'Risque', high: 'Élevé', medium: 'Moyen', low: 'Faible',
      items: 'Éléments', department: 'Service', submittedDate: 'Soumis le', issues: 'Points', allCompliant: 'Conforme',
      highRiskDetected: 'Risque élevé détecté', highRiskDesc: 'L\'IA a identifié 2 violations de politique à traiter avant approbation.',
      viewDetailsLink: 'Voir le détail →', expenseItems: 'Éléments de dépense', viewAll: 'Tout voir', policyViolations: 'Violations de politique',
      requestInfo: 'Demander des infos', submittedOn: 'Soumis le', riskLabel: 'Risque',
    },
  },
}

// Flatten for simple key lookup: "header.searchPlaceholder" -> string
function flatten(obj: Record<string, unknown>, prefix = ''): Record<string, string> {
  const result: Record<string, string> = {}
  for (const [k, v] of Object.entries(obj)) {
    const key = prefix ? `${prefix}.${k}` : k
    if (v && typeof v === 'object' && !Array.isArray(v)) {
      Object.assign(result, flatten(v as Record<string, unknown>, key))
    } else {
      result[key] = String(v)
    }
  }
  return result
}

const flatEn = flatten(translations.en as unknown as Record<string, unknown>)
const flatFr = flatten(translations.fr as unknown as Record<string, unknown>)

function getTranslation(locale: Locale, key: string): string {
  const flat = locale === 'fr' ? flatFr : flatEn
  return flat[key] ?? key
}

interface LanguageContextValue {
  locale: Locale
  setLocale: (locale: Locale) => void
  t: (key: string) => string
  localeVersion: number
  /** Translate dynamic text via LibreTranslate API. Cached per (text, locale). */
  translateText: (text: string) => Promise<string>
}

const LanguageContext = createContext<LanguageContextValue | null>(null)

const translateCache = new Map<string, string>()

export function LanguageProvider({ children }: { children: React.ReactNode }) {
  const [locale, setLocaleState] = useState<Locale>('fr')
  const [localeVersion, setLocaleVersion] = useState(0)
  const [mounted, setMounted] = useState(false)
  const cacheRef = useRef(translateCache)

  useEffect(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY) as Locale | null
      if (stored === 'en' || stored === 'fr') setLocaleState(stored)
    } catch (_) {}
    setMounted(true)
  }, [])

  useEffect(() => {
    if (!mounted) return
    try {
      localStorage.setItem(STORAGE_KEY, locale)
    } catch (_) {}
    if (typeof document !== 'undefined') {
      document.documentElement.lang = locale
    }
  }, [locale, mounted])

  const setLocale = useCallback((next: Locale) => {
    setLocaleState(next)
    setLocaleVersion((v) => v + 1)
  }, [])

  const t = useCallback(
    (key: string) => getTranslation(locale, key),
    [locale]
  )

  const translateText = useCallback(
    async (text: string): Promise<string> => {
      if (!text?.trim()) return text
      if (locale === 'en') return text
      const cacheKey = `${locale}:${text.trim()}`
      const cached = cacheRef.current.get(cacheKey)
      if (cached != null) return cached
      try {
        const translated = await translateWithAPI(text, locale)
        cacheRef.current.set(cacheKey, translated)
        return translated
      } catch {
        return text
      }
    },
    [locale]
  )

  const value = React.useMemo(
    () => ({ locale, setLocale, t, localeVersion, translateText }),
    [locale, setLocale, t, localeVersion, translateText]
  )

  return (
    <LanguageContext.Provider value={value}>
      <div key={`lang-${locale}-${localeVersion}`}>
        {children}
      </div>
    </LanguageContext.Provider>
  )
}

const defaultContext: LanguageContextValue = {
  locale: 'fr',
  setLocale: () => {},
  t: (key: string) => key,
  localeVersion: 0,
  translateText: (text: string) => Promise.resolve(text),
}

export function useLanguage() {
  const ctx = useContext(LanguageContext)
  if (!ctx) {
    if (typeof window !== 'undefined') {
      console.warn('useLanguage: LanguageProvider not found in tree. Wrap the app with <LanguageProvider>.')
    }
    return defaultContext
  }
  return ctx
}
