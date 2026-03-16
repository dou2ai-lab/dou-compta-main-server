'use client';

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { authAPI } from '@/lib/api';

interface User {
  id: string;
  email: string;
  first_name?: string;
  last_name?: string;
  tenant_id: string;
  roles: string[];
  permissions: string[];
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  loading: boolean;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (typeof window !== 'undefined') {
      const getCookie = (name: string): string | null => {
        const match = document.cookie.match(new RegExp(`(?:^|; )${name}=([^;]*)`));
        return match ? decodeURIComponent(match[1]) : null;
      };

      // Check for stored token and user (email/password login path)
      const storedToken = localStorage.getItem('token');
      const storedUser = localStorage.getItem('user');

      if (storedToken && storedUser) {
        setToken(storedToken);
        setUser(JSON.parse(storedUser));
        setLoading(false); // Don't block render on /me — avoid flash; verify in background
        authAPI.me()
          .then((userData) => {
            setUser(userData);
            localStorage.setItem('user', JSON.stringify(userData));
          })
          .catch(() => {
            localStorage.removeItem('token');
            localStorage.removeItem('user');
            setToken(null);
            setUser(null);
          });
      } else {
        // Fallback: support SSO sessions established via cookies only (Google/Microsoft/Okta).
        const cookieToken = getCookie('token');
        const cookieRefresh = getCookie('refresh_token');

        if (!cookieToken) {
          setLoading(false);
          return;
        }

        setToken(cookieToken);
        authAPI.me()
          .then((userData) => {
            setUser(userData);
            // Persist to localStorage so the rest of the app behaves the same as password login.
            localStorage.setItem('user', JSON.stringify(userData));
            localStorage.setItem('token', cookieToken);
            if (cookieRefresh) {
              localStorage.setItem('refresh_token', cookieRefresh);
            }
          })
          .catch(() => {
            localStorage.removeItem('token');
            localStorage.removeItem('refresh_token');
            localStorage.removeItem('user');
            setToken(null);
            setUser(null);
          })
          .finally(() => {
            setLoading(false);
          });
      }
    }
  }, []);

  const login = async (email: string, password: string) => {
    try {
      const response = await authAPI.login(email, password);
      
      // authAPI.login returns: {token, refresh_token, user}
      const { token: newToken, refresh_token, user: newUser } = response || {};
      
      if (!newToken || !newUser) {
        throw new Error('Invalid login response: missing token or user data');
      }

      // Use the real JWT from login so expense (and other) services see the actual user and roles (RBAC).
      if (typeof window !== 'undefined') {
        localStorage.setItem('token', newToken);
        if (refresh_token) {
          localStorage.setItem('refresh_token', refresh_token);
        }
        localStorage.setItem('user', JSON.stringify(newUser));

        const maxAge = 30 * 60; // 30 minutes in seconds
        document.cookie = `token=${encodeURIComponent(newToken)}; path=/; max-age=${maxAge}; SameSite=Lax`;
      }

      setToken(newToken);
      setUser(newUser);
    } catch (error) {
      console.error('Login error:', error);
      throw error;
    }
  };

  const logout = async () => {
    try {
      await authAPI.logout();
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      setToken(null);
      setUser(null);
      if (typeof window !== 'undefined') {
        localStorage.removeItem('token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('user');
        // Clear the cookies set by the auth service (including OAuth callback)
        document.cookie = 'token=; path=/; max-age=0; SameSite=Lax';
        document.cookie = 'refresh_token=; path=/; max-age=0; SameSite=Lax';
      }
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        login,
        logout,
        loading,
        isAuthenticated: !!user && !!token,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}





