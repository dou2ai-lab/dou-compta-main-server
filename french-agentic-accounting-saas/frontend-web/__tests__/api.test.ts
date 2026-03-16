/**
 * Tests for API client module.
 * Validates that all API objects are properly exported and have the correct methods.
 */
import {
  authAPI, expensesAPI, accountingAPI, dossierAPI, notificationAPI,
  bankingAPI, taxAPI, analysisAPI, einvoiceAPI, payrollAPI, collectionAPI, agentsAPI,
} from '../lib/api'

describe('API Client Exports', () => {
  describe('accountingAPI', () => {
    it('has all required methods', () => {
      expect(accountingAPI.listEntries).toBeDefined()
      expect(accountingAPI.getEntry).toBeDefined()
      expect(accountingAPI.generateFromExpense).toBeDefined()
      expect(accountingAPI.validateEntry).toBeDefined()
      expect(accountingAPI.getTrialBalance).toBeDefined()
      expect(accountingAPI.exportFEC).toBeDefined()
      expect(accountingAPI.listPCGAccounts).toBeDefined()
      expect(accountingAPI.seedPCGAccounts).toBeDefined()
      expect(accountingAPI.listThirdParties).toBeDefined()
      expect(accountingAPI.listPeriods).toBeDefined()
    })
  })

  describe('dossierAPI', () => {
    it('has all required methods', () => {
      expect(dossierAPI.list).toBeDefined()
      expect(dossierAPI.get).toBeDefined()
      expect(dossierAPI.create).toBeDefined()
      expect(dossierAPI.update).toBeDefined()
      expect(dossierAPI.getSummary).toBeDefined()
      expect(dossierAPI.getTimeline).toBeDefined()
      expect(dossierAPI.listDocuments).toBeDefined()
    })
  })

  describe('notificationAPI', () => {
    it('has all required methods', () => {
      expect(notificationAPI.list).toBeDefined()
      expect(notificationAPI.markRead).toBeDefined()
      expect(notificationAPI.markAllRead).toBeDefined()
      expect(notificationAPI.getUnreadCount).toBeDefined()
    })
  })

  describe('bankingAPI', () => {
    it('has all required methods', () => {
      expect(bankingAPI.listAccounts).toBeDefined()
      expect(bankingAPI.createAccount).toBeDefined()
      expect(bankingAPI.listTransactions).toBeDefined()
      expect(bankingAPI.matchTransaction).toBeDefined()
      expect(bankingAPI.unmatchTransaction).toBeDefined()
      expect(bankingAPI.reconcile).toBeDefined()
      expect(bankingAPI.uploadStatement).toBeDefined()
    })
  })

  describe('taxAPI', () => {
    it('has all required methods', () => {
      expect(taxAPI.listDeclarations).toBeDefined()
      expect(taxAPI.getDeclaration).toBeDefined()
      expect(taxAPI.computeDeclaration).toBeDefined()
      expect(taxAPI.validateDeclaration).toBeDefined()
      expect(taxAPI.getCalendar).toBeDefined()
      expect(taxAPI.getPenalties).toBeDefined()
    })
  })

  describe('analysisAPI', () => {
    it('has all required methods', () => {
      expect(analysisAPI.getSIG).toBeDefined()
      expect(analysisAPI.getRatios).toBeDefined()
      expect(analysisAPI.getScoring).toBeDefined()
      expect(analysisAPI.createForecast).toBeDefined()
      expect(analysisAPI.listScenarios).toBeDefined()
    })
  })

  describe('einvoiceAPI', () => {
    it('has all required methods', () => {
      expect(einvoiceAPI.list).toBeDefined()
      expect(einvoiceAPI.get).toBeDefined()
      expect(einvoiceAPI.create).toBeDefined()
    })
  })

  describe('payrollAPI', () => {
    it('has all required methods', () => {
      expect(payrollAPI.allocateCharges).toBeDefined()
      expect(payrollAPI.getAccounts).toBeDefined()
    })
  })

  describe('collectionAPI', () => {
    it('has all required methods', () => {
      expect(collectionAPI.classify).toBeDefined()
      expect(collectionAPI.getDocumentTypes).toBeDefined()
    })
  })

  describe('agentsAPI', () => {
    it('has all required methods', () => {
      expect(agentsAPI.listTasks).toBeDefined()
      expect(agentsAPI.toggleTask).toBeDefined()
      expect(agentsAPI.getStatus).toBeDefined()
    })
  })
})
