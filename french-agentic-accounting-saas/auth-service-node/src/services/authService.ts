/**
 * Auth business logic: signup, login, refresh, user profile.
 * Constant-time compare for passwords to mitigate timing attacks.
 */
import bcrypt from 'bcrypt';
import jwt from 'jsonwebtoken';
import { PrismaClient } from '@prisma/client';
import { config } from '../config';
import type { SignupBody, LoginBody, ForgotPasswordBody, ResetPasswordBody } from '../validators/auth';

const RESET_TOKEN_EXPIRY_MS = 60 * 60 * 1000; // 1 hour

const prisma = new PrismaClient();

const SALT_ROUNDS = 12;

export async function hashPassword(password: string): Promise<string> {
  return bcrypt.hash(password, SALT_ROUNDS);
}

export async function verifyPassword(password: string, hash: string): Promise<boolean> {
  return bcrypt.compare(password, hash);
}

export function createAccessToken(payload: { sub: string; email: string; tenantId: string; roles: string[] }): string {
  return jwt.sign(
    { ...payload, type: 'access' },
    config.jwt.secret,
    { expiresIn: config.jwt.accessExpiresIn }
  );
}

export function createRefreshToken(payload: { sub: string }): string {
  return jwt.sign(
    { ...payload, type: 'refresh' },
    config.jwt.refreshSecret,
    { expiresIn: config.jwt.refreshExpiresIn }
  );
}

export function verifyAccessToken(token: string): { sub: string; email: string; tenantId: string; roles: string[] } | null {
  try {
    const decoded = jwt.verify(token, config.jwt.secret) as any;
    if (decoded?.type !== 'access') return null;
    return {
      sub: decoded.sub,
      email: decoded.email,
      tenantId: decoded.tenantId,
      roles: Array.isArray(decoded.roles) ? decoded.roles : [],
    };
  } catch {
    return null;
  }
}

export function verifyRefreshToken(token: string): { sub: string } | null {
  try {
    const decoded = jwt.verify(token, config.jwt.refreshSecret) as any;
    if (decoded?.type !== 'refresh') return null;
    return { sub: decoded.sub };
  } catch {
    return null;
  }
}

/** Hash for storing tokens (never store plaintext). */
export function hashToken(token: string): string {
  const crypto = require('crypto');
  return crypto.createHash('sha256').update(token).digest('hex');
}
function hashRefreshToken(token: string): string {
  return hashToken(token);
}

export function toUserResponse(user: {
  id: string;
  email: string;
  firstName: string | null;
  lastName: string | null;
  tenantId: string;
}) {
  return {
    id: user.id,
    email: user.email,
    first_name: user.firstName ?? undefined,
    last_name: user.lastName ?? undefined,
    tenant_id: user.tenantId,
    roles: ['Employee'] as string[],
    permissions: [] as string[],
  };
}

/** Get or create default tenant. */
export async function getOrCreateDefaultTenant() {
  let tenant = await prisma.tenant.findFirst({ where: { slug: 'default' } });
  if (!tenant) {
    tenant = await prisma.tenant.create({
      data: { name: 'Default Tenant', slug: 'default', status: 'active' },
    });
  }
  return tenant;
}

export async function signup(body: SignupBody) {
  const existing = await prisma.user.findUnique({ where: { email: body.email.toLowerCase().trim() } });
  if (existing) {
    throw new Error('EMAIL_EXISTS'); // French message in controller
  }

  const tenant = await getOrCreateDefaultTenant();
  const passwordHash = await hashPassword(body.password);
  const user = await prisma.user.create({
    data: {
      email: body.email.toLowerCase().trim(),
      passwordHash,
      firstName: body.first_name?.trim() || null,
      lastName: body.last_name?.trim() || null,
      tenantId: tenant.id,
      status: 'active',
    },
  });

  const roles = ['Employee'];
  const accessToken = createAccessToken({
    sub: user.id,
    email: user.email,
    tenantId: user.tenantId,
    roles,
  });
  const refreshToken = createRefreshToken({ sub: user.id });
  await prisma.refreshToken.create({
    data: {
      userId: user.id,
      tokenHash: hashRefreshToken(refreshToken),
      expiresAt: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000),
    },
  });

  return {
    token: accessToken,
    refresh_token: refreshToken,
    user: toUserResponse(user),
  };
}

/**
 * Login or sign up a user coming from an OAuth/OIDC provider.
 * Normalizes email, creates user under default tenant if needed, and issues tokens.
 */
export async function ssoLoginOrSignup(email: string, firstName?: string, lastName?: string) {
  const normalizedEmail = email.toLowerCase().trim();

  let user = await prisma.user.findUnique({
    where: { email: normalizedEmail },
    include: { tenant: true },
  });

  if (!user) {
    const tenant = await getOrCreateDefaultTenant();
    const crypto = require('crypto');
    const randomPassword = crypto.randomBytes(16).toString('hex');
    const passwordHash = await hashPassword(randomPassword);

    user = await prisma.user.create({
      data: {
        email: normalizedEmail,
        passwordHash,
        firstName: firstName?.trim() || null,
        lastName: lastName?.trim() || null,
        tenantId: tenant.id,
        status: 'active',
        isEmailVerified: true,
      },
      include: { tenant: true },
    });
  }

  if (!user.tenant || user.tenant.status !== 'active') {
    throw new Error('TENANT_INACTIVE');
  }
  if (user.status !== 'active') {
    throw new Error('USER_INACTIVE');
  }

  await prisma.user.update({
    where: { id: user.id },
    data: { lastLoginAt: new Date() },
  });

  const roles = ['Employee'];
  const accessToken = createAccessToken({
    sub: user.id,
    email: user.email,
    tenantId: user.tenantId,
    roles,
  });
  const refreshToken = createRefreshToken({ sub: user.id });

  await prisma.refreshToken.create({
    data: {
      userId: user.id,
      tokenHash: hashRefreshToken(refreshToken),
      expiresAt: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000),
    },
  });

  return {
    token: accessToken,
    refresh_token: refreshToken,
    user: toUserResponse(user),
  };
}

export async function login(body: LoginBody) {
  const user = await prisma.user.findUnique({
    where: { email: body.email.toLowerCase().trim() },
    include: { tenant: true },
  });
  if (!user || user.status !== 'active') {
    throw new Error('INVALID_CREDENTIALS');
  }
  if (!user.tenant || user.tenant.status !== 'active') {
    throw new Error('TENANT_INACTIVE');
  }

  const valid = await verifyPassword(body.password, user.passwordHash);
  if (!valid) {
    throw new Error('INVALID_CREDENTIALS');
  }

  await prisma.user.update({
    where: { id: user.id },
    data: { lastLoginAt: new Date() },
  });

  const roles = ['Employee'];
  const accessToken = createAccessToken({
    sub: user.id,
    email: user.email,
    tenantId: user.tenantId,
    roles,
  });
  const refreshToken = createRefreshToken({ sub: user.id });
  await prisma.refreshToken.create({
    data: {
      userId: user.id,
      tokenHash: hashRefreshToken(refreshToken),
      expiresAt: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000),
    },
  });

  return {
    token: accessToken,
    refresh_token: refreshToken,
    user: toUserResponse(user),
  };
}

export async function refresh(refreshToken: string) {
  const payload = verifyRefreshToken(refreshToken);
  if (!payload) throw new Error('INVALID_REFRESH_TOKEN');

  const hash = hashRefreshToken(refreshToken);
  const stored = await prisma.refreshToken.findFirst({
    where: { tokenHash: hash, userId: payload.sub },
    include: { user: true },
  });
  if (!stored || stored.expiresAt < new Date()) {
    if (stored) await prisma.refreshToken.delete({ where: { id: stored.id } }).catch(() => {});
    throw new Error('INVALID_REFRESH_TOKEN');
  }

  const user = stored.user;
  if (user.status !== 'active') throw new Error('USER_INACTIVE');

  const roles = ['Employee'];
  const accessToken = createAccessToken({
    sub: user.id,
    email: user.email,
    tenantId: user.tenantId,
    roles,
  });

  return { access_token: accessToken };
}

export async function getMe(userId: string) {
  const user = await prisma.user.findUnique({
    where: { id: userId },
    include: { tenant: true },
  });
  if (!user || user.status !== 'active') return null;
  return toUserResponse(user);
}

/** Generate a secure random token for password reset. */
function generateResetToken(): string {
  const crypto = require('crypto');
  return crypto.randomBytes(32).toString('hex');
}

/**
 * Request password reset: create token, store hash, return success.
 * Do not reveal whether the email exists (GDPR / security).
 * In dev, optionally return reset_link for testing (no real email sent).
 */
export async function requestPasswordReset(body: ForgotPasswordBody) {
  const email = body.email.toLowerCase().trim();
  const user = await prisma.user.findUnique({ where: { email }, include: { tenant: true } });
  if (!user || user.status !== 'active' || !user.tenant || user.tenant.status !== 'active') {
    return { success: true, message: 'Si un compte existe avec cet email, vous recevrez un lien de réinitialisation.' };
  }

  const rawToken = generateResetToken();
  const tokenHash = hashToken(rawToken);
  const expiresAt = new Date(Date.now() + RESET_TOKEN_EXPIRY_MS);

  await prisma.passwordResetToken.deleteMany({ where: { userId: user.id } });
  await prisma.passwordResetToken.create({
    data: { userId: user.id, tokenHash, expiresAt },
  });

  // Stub: no real email. In production, send email with link containing rawToken.
  // For dev/testing, return reset_link so frontend can redirect user.
  const isDev = process.env.NODE_ENV !== 'production';
  return {
    success: true,
    message: 'Si un compte existe avec cet email, vous recevrez un lien de réinitialisation.',
    ...(isDev && { reset_token: rawToken }),
  };
}

/**
 * Reset password with token: validate token, update password, delete token.
 */
export async function resetPassword(body: ResetPasswordBody) {
  const tokenHash = hashToken(body.token);
  const record = await prisma.passwordResetToken.findFirst({
    where: { tokenHash },
    include: { user: true },
  });
  if (!record || record.expiresAt < new Date()) {
    throw new Error('INVALID_RESET_TOKEN');
  }

  const user = record.user;
  if (user.status !== 'active') throw new Error('USER_INACTIVE');

  const passwordHash = await hashPassword(body.new_password);
  await prisma.$transaction([
    prisma.user.update({ where: { id: user.id }, data: { passwordHash, updatedAt: new Date() } }),
    prisma.passwordResetToken.delete({ where: { id: record.id } }),
  ]);

  return { success: true, message: 'Votre mot de passe a été réinitialisé. Vous pouvez vous connecter.' };
}
