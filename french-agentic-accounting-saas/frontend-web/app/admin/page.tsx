'use client';

import React, { useState, useEffect } from 'react';
import { adminAPI } from '@/lib/api';

export default function AdminPage() {
  const [activeTab, setActiveTab] = useState<'policies' | 'vat' | 'users'>('users');
  const [users, setUsers] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (activeTab === 'users') {
      loadUsers();
    }
  }, [activeTab]);

  const loadUsers = async () => {
    try {
      setLoading(true);
      const response = await adminAPI.users();
      setUsers(response.data?.users || []);
    } catch (err: any) {
      console.error('Failed to load users:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <div className="max-w-7xl mx-auto">
        <h1 className="text-3xl font-bold text-gray-900 mb-6">Admin Panel</h1>

        <div className="bg-white shadow rounded-lg">
          <div className="border-b border-gray-200">
            <nav className="flex -mb-px">
              <button
                onClick={() => setActiveTab('users')}
                className={`px-6 py-3 text-sm font-medium ${
                  activeTab === 'users'
                    ? 'border-b-2 border-blue-500 text-blue-600'
                    : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                Users
              </button>
              <button
                onClick={() => setActiveTab('policies')}
                className={`px-6 py-3 text-sm font-medium ${
                  activeTab === 'policies'
                    ? 'border-b-2 border-blue-500 text-blue-600'
                    : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                Policies
              </button>
              <button
                onClick={() => setActiveTab('vat')}
                className={`px-6 py-3 text-sm font-medium ${
                  activeTab === 'vat'
                    ? 'border-b-2 border-blue-500 text-blue-600'
                    : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                VAT Rules
              </button>
            </nav>
          </div>

          <div className="p-6">
            {activeTab === 'users' && (
              <div>
                <h2 className="text-xl font-semibold mb-4">Users</h2>
                {loading ? (
                  <div>Loading...</div>
                ) : (
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Name</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Email</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {users.map((user) => (
                        <tr key={user.id}>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            {user.first_name} {user.last_name}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            {user.email}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                            {user.status}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
              </div>
            )}

            {activeTab === 'policies' && (
              <div>
                <h2 className="text-xl font-semibold mb-4">Expense Policies</h2>
                <div className="mb-4">
                  <button
                    onClick={() => {
                      // TODO: Implement policy creation modal/form
                      alert('Policy creation form will be implemented soon');
                    }}
                    className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                  >
                    Create Policy
                  </button>
                </div>
                <div className="bg-white rounded-lg border border-gray-200">
                  <div className="p-6 text-center text-gray-500">
                    <p className="mb-2">No policies configured yet.</p>
                    <p className="text-sm">Policies help enforce spending rules and compliance requirements.</p>
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'vat' && (
              <div>
                <h2 className="text-lg font-semibold mb-4">VAT Rules & Categories</h2>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {/* Categories Section */}
                  <div>
                    <h3 className="text-md font-semibold mb-3">Expense Categories</h3>
                    <div className="bg-white rounded-lg border border-gray-200 p-4">
                      <div className="mb-3">
                        <button
                          onClick={() => {
                            const categoryName = prompt('Enter category name:');
                            if (categoryName) {
                              // TODO: Implement category creation API call
                              alert(`Category "${categoryName}" creation will be implemented soon`);
                            }
                          }}
                          className="px-3 py-1 bg-blue-600 text-white text-sm rounded hover:bg-blue-700"
                        >
                          Add Category
                        </button>
                      </div>
                      <div className="space-y-2 text-sm text-gray-600">
                        <div className="flex justify-between items-center py-2 border-b">
                          <span>Travel & Transport</span>
                          <span className="text-xs text-gray-500">20% VAT</span>
                        </div>
                        <div className="flex justify-between items-center py-2 border-b">
                          <span>Meals & Entertainment</span>
                          <span className="text-xs text-gray-500">20% VAT</span>
                        </div>
                        <div className="flex justify-between items-center py-2 border-b">
                          <span>Office Supplies</span>
                          <span className="text-xs text-gray-500">20% VAT</span>
                        </div>
                        <div className="flex justify-between items-center py-2">
                          <span>Accommodation</span>
                          <span className="text-xs text-gray-500">10% VAT</span>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* GL Accounts Section */}
                  <div>
                    <h3 className="text-md font-semibold mb-3">GL Accounts</h3>
                    <div className="bg-white rounded-lg border border-gray-200 p-4">
                      <div className="mb-3">
                        <button
                          onClick={() => {
                            const accountCode = prompt('Enter GL Account Code:');
                            const accountName = prompt('Enter GL Account Name:');
                            if (accountCode && accountName) {
                              // TODO: Implement GL account creation API call
                              alert(`GL Account "${accountCode} - ${accountName}" creation will be implemented soon`);
                            }
                          }}
                          className="px-3 py-1 bg-blue-600 text-white text-sm rounded hover:bg-blue-700"
                        >
                          Add GL Account
                        </button>
                      </div>
                      <div className="space-y-2 text-sm text-gray-600">
                        <div className="flex justify-between items-center py-2 border-b">
                          <div>
                            <div className="font-medium">6000 - Travel</div>
                            <div className="text-xs text-gray-500">Expense Account</div>
                          </div>
                        </div>
                        <div className="flex justify-between items-center py-2 border-b">
                          <div>
                            <div className="font-medium">6100 - Meals</div>
                            <div className="text-xs text-gray-500">Expense Account</div>
                          </div>
                        </div>
                        <div className="flex justify-between items-center py-2">
                          <div>
                            <div className="font-medium">6200 - Office</div>
                            <div className="text-xs text-gray-500">Expense Account</div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                {/* VAT Rates Section */}
                <div className="mt-6">
                  <h3 className="text-md font-semibold mb-3">VAT Rates (France)</h3>
                  <div className="bg-white rounded-lg border border-gray-200 p-4">
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 text-sm">
                      <div className="border-l-4 border-blue-500 pl-3">
                        <div className="font-semibold text-lg">20%</div>
                        <div className="text-gray-600">Standard Rate</div>
                        <div className="text-xs text-gray-500 mt-1">Most goods & services</div>
                      </div>
                      <div className="border-l-4 border-green-500 pl-3">
                        <div className="font-semibold text-lg">10%</div>
                        <div className="text-gray-600">Intermediate Rate</div>
                        <div className="text-xs text-gray-500 mt-1">Restaurants, hotels</div>
                      </div>
                      <div className="border-l-4 border-yellow-500 pl-3">
                        <div className="font-semibold text-lg">5.5%</div>
                        <div className="text-gray-600">Reduced Rate</div>
                        <div className="text-xs text-gray-500 mt-1">Food, books, transport</div>
                      </div>
                      <div className="border-l-4 border-purple-500 pl-3">
                        <div className="font-semibold text-lg">2.1%</div>
                        <div className="text-gray-600">Super-Reduced Rate</div>
                        <div className="text-xs text-gray-500 mt-1">Medicines, newspapers</div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </>
  );
}












