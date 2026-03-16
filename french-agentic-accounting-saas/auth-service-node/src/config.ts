/**
 * Environment and app config.
 * All secrets from env; no defaults for production.
 */
import dotenv from 'dotenv';

dotenv.config();

const required = (key: string): string => {
  const v = process.env[key];
  if (!v) throw new Error(`Missing required env: ${key}`);
  return v;
};

export const config = {
  port: parseInt(process.env.PORT || '8001', 10),
  nodeEnv: process.env.NODE_ENV || 'development',
  jwt: {
    secret: required('JWT_SECRET'),
    refreshSecret: required('JWT_REFRESH_SECRET'),
    accessExpiresIn: process.env.JWT_ACCESS_EXPIRES_IN || '30m',
    refreshExpiresIn: process.env.JWT_REFRESH_EXPIRES_IN || '7d',
  },
  database: {
    url: required('DATABASE_URL'),
  },
  rateLimit: {
    windowMs: 15 * 60 * 1000, // 15 min
    max: 100, // per IP
    authWindowMs: 15 * 60 * 1000,
    authMax: 10, // login/signup attempts per 15 min
  },
  oauth: {
    google: {
      clientId: process.env.GOOGLE_CLIENT_ID,
      clientSecret: process.env.GOOGLE_CLIENT_SECRET,
      redirectUri: process.env.GOOGLE_REDIRECT_URI,
    },
    microsoft: {
      clientId: process.env.MICROSOFT_CLIENT_ID,
      clientSecret: process.env.MICROSOFT_CLIENT_SECRET,
      tenantId: process.env.MICROSOFT_TENANT_ID,
      redirectUri: process.env.MICROSOFT_REDIRECT_URI,
    },
    okta: {
      clientId: process.env.OKTA_CLIENT_ID,
      clientSecret: process.env.OKTA_CLIENT_SECRET,
      issuer: process.env.OKTA_ISSUER,
      redirectUri: process.env.OKTA_REDIRECT_URI,
    },
    frontendUrl: process.env.FRONTEND_APP_URL || 'http://localhost:3000',
  },
} as const;
