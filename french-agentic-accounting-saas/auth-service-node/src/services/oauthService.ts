import type { Request } from 'express';
import { Issuer, Client, generators } from 'openid-client';
import { config } from '../config';
import * as authService from './authService';

type Provider = 'google' | 'microsoft' | 'okta';

type ProviderConfig =
  | {
      clientId: string;
      clientSecret: string;
      redirectUri: string;
      issuerUrl: string;
    }
  | null;

let googleClientPromise: Promise<Client> | null = null;
let microsoftClientPromise: Promise<Client> | null = null;
let oktaClientPromise: Promise<Client> | null = null;

const stateStore = new Map<
  string,
  {
    provider: Provider;
    codeVerifier: string;
  }
>();

function getProviderConfig(provider: Provider): ProviderConfig {
  if (provider === 'google') {
    const { clientId, clientSecret, redirectUri } = config.oauth.google;
    if (!clientId || !clientSecret || !redirectUri) return null;
    return {
      clientId,
      clientSecret,
      redirectUri,
      issuerUrl: 'https://accounts.google.com',
    };
  }

  if (provider === 'microsoft') {
    const { clientId, clientSecret, tenantId, redirectUri } = config.oauth.microsoft;
    if (!clientId || !clientSecret || !redirectUri) return null;
    const tenant = tenantId || 'common';
    return {
      clientId,
      clientSecret,
      redirectUri,
      issuerUrl: `https://login.microsoftonline.com/${tenant}/v2.0`,
    };
  }

  if (provider === 'okta') {
    const { clientId, clientSecret, issuer, redirectUri } = config.oauth.okta;
    if (!clientId || !clientSecret || !issuer || !redirectUri) return null;
    return {
      clientId,
      clientSecret,
      redirectUri,
      issuerUrl: issuer,
    };
  }

  return null;
}

async function getClient(provider: Provider): Promise<Client> {
  const cfg = getProviderConfig(provider);
  if (!cfg) {
    throw new Error(`OAUTH_NOT_CONFIGURED_${provider.toUpperCase()}`);
  }

  if (provider === 'google') {
    if (!googleClientPromise) {
      googleClientPromise = (async () => {
        const issuer = await Issuer.discover(cfg.issuerUrl);
        return new issuer.Client({
          client_id: cfg.clientId,
          client_secret: cfg.clientSecret,
          redirect_uris: [cfg.redirectUri],
          response_types: ['code'],
        });
      })();
    }
    return googleClientPromise;
  }

  if (provider === 'microsoft') {
    if (!microsoftClientPromise) {
      microsoftClientPromise = (async () => {
        const issuer = await Issuer.discover(cfg.issuerUrl);
        return new issuer.Client({
          client_id: cfg.clientId,
          client_secret: cfg.clientSecret,
          redirect_uris: [cfg.redirectUri],
          response_types: ['code'],
        });
      })();
    }
    return microsoftClientPromise;
  }

  if (provider === 'okta') {
    if (!oktaClientPromise) {
      oktaClientPromise = (async () => {
        const issuer = await Issuer.discover(cfg.issuerUrl);
        return new issuer.Client({
          client_id: cfg.clientId,
          client_secret: cfg.clientSecret,
          redirect_uris: [cfg.redirectUri],
          response_types: ['code'],
        });
      })();
    }
    return oktaClientPromise;
  }

  // Should be unreachable
  throw new Error('UNKNOWN_PROVIDER');
}

function getRedirectUri(provider: Provider): string {
  const cfg = getProviderConfig(provider);
  if (!cfg) {
    throw new Error(`OAUTH_NOT_CONFIGURED_${provider.toUpperCase()}`);
  }
  return cfg.redirectUri;
}

export async function getAuthorizationUrl(provider: Provider): Promise<string> {
  const client = await getClient(provider);

  const codeVerifier = generators.codeVerifier();
  const codeChallenge = generators.codeChallenge(codeVerifier);
  const state = generators.state();

  stateStore.set(state, { provider, codeVerifier });

  const url = client.authorizationUrl({
    scope: 'openid email profile',
    code_challenge: codeChallenge,
    code_challenge_method: 'S256',
    state,
  });

  return url;
}

export async function handleCallback(provider: Provider, req: Request) {
  const client = await getClient(provider);
  const params = client.callbackParams(req);

  const state = (params.state as string) || '';
  const stored = stateStore.get(state);
  if (!stored || stored.provider !== provider) {
    throw new Error('INVALID_OAUTH_STATE');
  }
  stateStore.delete(state);

  const redirectUri = getRedirectUri(provider);

  const tokenSet = await client.callback(redirectUri, params, { state }, { code_verifier: stored.codeVerifier });

  const claims = tokenSet.claims();

  // Prefer userinfo endpoint when available, else use ID token claims.
  let profile: any = claims;
  if (tokenSet.access_token) {
    try {
      const userinfo = await client.userinfo(tokenSet.access_token);
      profile = { ...claims, ...userinfo };
    } catch {
      // Fallback: use claims only.
    }
  }

  const email =
    (profile.email as string | undefined) ||
    (profile.preferred_username as string | undefined) ||
    (profile.upn as string | undefined);

  if (!email) {
    throw new Error('OAUTH_MISSING_EMAIL');
  }

  const firstName = (profile.given_name as string | undefined) ?? undefined;
  const lastName = (profile.family_name as string | undefined) ?? undefined;

  const result = await authService.ssoLoginOrSignup(email, firstName, lastName);

  return result;
}

