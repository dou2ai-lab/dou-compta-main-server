/**
 * Auth HTTP handlers. Return shapes match frontend expectations.
 */
import { Request, Response, NextFunction } from 'express';
import { signupSchema, loginSchema, refreshSchema, forgotPasswordSchema, resetPasswordSchema } from '../validators/auth';
import * as authService from '../services/authService';
import * as oauthService from '../services/oauthService';
import { config } from '../config';

// French-friendly messages (GDPR / UX)
const MESSAGES: Record<string, string> = {
  EMAIL_EXISTS: 'Un compte existe déjà avec cette adresse email.',
  INVALID_CREDENTIALS: 'Email ou mot de passe incorrect.',
  TENANT_INACTIVE: 'Compte organisation inactif.',
  INVALID_REFRESH_TOKEN: 'Session expirée. Veuillez vous reconnecter.',
  USER_INACTIVE: 'Compte utilisateur inactif.',
  INVALID_RESET_TOKEN: 'Lien de réinitialisation invalide ou expiré. Veuillez demander un nouveau lien.',
};

function sendError(res: Response, code: string, statusCode: number, message?: string) {
  res.status(statusCode).json({
    success: false,
    code,
    message: message ?? MESSAGES[code] ?? 'Une erreur est survenue.',
  });
}

export async function signup(req: Request, res: Response, next: NextFunction) {
  try {
    const parsed = signupSchema.safeParse(req);
    if (!parsed.success) {
      const msg = parsed.error.errors.map((e) => e.message).join(' ');
      return res.status(400).json({ success: false, code: 'VALIDATION_ERROR', message: msg });
    }
    const result = await authService.signup(parsed.data.body);
    res.status(201).json({ success: true, data: result });
  } catch (e: any) {
    if (e.message === 'EMAIL_EXISTS') {
      return sendError(res, 'EMAIL_EXISTS', 400);
    }
    next(e);
  }
}

export async function login(req: Request, res: Response, next: NextFunction) {
  try {
    const parsed = loginSchema.safeParse(req);
    if (!parsed.success) {
      const msg = parsed.error.errors.map((e) => e.message).join(' ');
      return res.status(400).json({ success: false, code: 'VALIDATION_ERROR', message: msg });
    }
    const result = await authService.login(parsed.data.body);
    res.json({ success: true, data: result });
  } catch (e: any) {
    if (e.message === 'INVALID_CREDENTIALS' || e.message === 'TENANT_INACTIVE' || e.message === 'USER_INACTIVE') {
      return sendError(res, e.message, 401);
    }
    next(e);
  }
}

export async function logout(_req: Request, res: Response) {
  res.json({ success: true, data: null });
}

export async function refresh(req: Request, res: Response, next: NextFunction) {
  try {
    const parsed = refreshSchema.safeParse(req);
    if (!parsed.success) {
      return res.status(400).json({
        success: false,
        code: 'VALIDATION_ERROR',
        message: parsed.error.errors.map((e) => e.message).join(' '),
      });
    }
    const result = await authService.refresh(parsed.data.body.refresh_token);
    res.json(result);
  } catch (e: any) {
    if (e.message === 'INVALID_REFRESH_TOKEN' || e.message === 'USER_INACTIVE') {
      return sendError(res, 'INVALID_REFRESH_TOKEN', 401);
    }
    next(e);
  }
}

export async function me(req: Request, res: Response, next: NextFunction) {
  try {
    const userId = (req as any).userId;
    if (!userId) return sendError(res, 'UNAUTHORIZED', 401);
    const user = await authService.getMe(userId);
    if (!user) return sendError(res, 'USER_NOT_FOUND', 404);
    res.json(user);
  } catch (e) {
    next(e);
  }
}

export async function forgotPassword(req: Request, res: Response, next: NextFunction) {
  try {
    const parsed = forgotPasswordSchema.safeParse(req);
    if (!parsed.success) {
      const msg = parsed.error.errors.map((e) => e.message).join(' ');
      return res.status(400).json({ success: false, code: 'VALIDATION_ERROR', message: msg });
    }
    const result = await authService.requestPasswordReset(parsed.data.body);
    res.json(result);
  } catch (e) {
    next(e);
  }
}

export async function resetPassword(req: Request, res: Response, next: NextFunction) {
  try {
    const parsed = resetPasswordSchema.safeParse(req);
    if (!parsed.success) {
      const msg = parsed.error.errors.map((e) => e.message).join(' ');
      return res.status(400).json({ success: false, code: 'VALIDATION_ERROR', message: msg });
    }
    const result = await authService.resetPassword(parsed.data.body);
    res.json(result);
  } catch (e: any) {
    if (e.message === 'INVALID_RESET_TOKEN' || e.message === 'USER_INACTIVE') {
      return sendError(res, 'INVALID_RESET_TOKEN', 400);
    }
    next(e);
  }
}

function normalizeProvider(raw: string): 'google' | 'microsoft' | 'okta' {
  const value = raw.toLowerCase();
  if (value === 'google') return 'google';
  if (value === 'microsoft' || value === 'azure' || value === 'azuread' || value === 'azure-ad') return 'microsoft';
  if (value === 'okta') return 'okta';
  throw new Error('UNSUPPORTED_OAUTH_PROVIDER');
}

export async function oauthStart(req: Request, res: Response, next: NextFunction) {
  try {
    const provider = normalizeProvider(req.params.provider);
    const url = await oauthService.getAuthorizationUrl(provider);
    res.redirect(url);
  } catch (e) {
    next(e);
  }
}

export async function oauthCallback(req: Request, res: Response, next: NextFunction) {
  try {
    const provider = normalizeProvider(req.params.provider);
    const result = await oauthService.handleCallback(provider, req);

    const secure = config.nodeEnv === 'production';

    // Align cookie semantics with frontend login (non-HTTP-only, SameSite=Lax).
    res.cookie('token', result.token, {
      httpOnly: false,
      sameSite: 'lax',
      secure,
      path: '/',
      maxAge: 30 * 60 * 1000, // 30 minutes
    });

    res.cookie('refresh_token', result.refresh_token, {
      httpOnly: false,
      sameSite: 'lax',
      secure,
      path: '/',
      maxAge: 7 * 24 * 60 * 60 * 1000, // 7 days
    });

    const redirectBase = config.oauth.frontendUrl || 'http://localhost:3000';
    // After SSO, send the user to the main app; RootLayout + Home will route appropriately.
    res.redirect(`${redirectBase}/`);
  } catch (e) {
    const redirectBase = config.oauth.frontendUrl || 'http://localhost:3000';
    const params = new URLSearchParams({ error: 'sso_failed' });
    res.redirect(`${redirectBase}/login?${params.toString()}`);
    next(e);
  }
}
