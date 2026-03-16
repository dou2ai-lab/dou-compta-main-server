/**
 * Centralized error handler. Always returns { success: false, code, message }.
 * Technical errors (DB, Prisma, etc.) are logged only; user gets a safe message.
 */
import { Request, Response, NextFunction } from 'express';

const SAFE_USER_MESSAGE = 'Le service est temporairement indisponible. Veuillez réessayer plus tard.';

function isTechnicalError(message: string): boolean {
  const lower = message.toLowerCase();
  return (
    lower.includes('prisma') ||
    lower.includes('invocation') ||
    lower.includes('does not exist') ||
    lower.includes('table') ||
    lower.includes('database') ||
    lower.includes('connection') ||
    lower.includes('schema') ||
    lower.includes('migration')
  );
}

export function errorHandler(err: any, _req: Request, res: Response, _next: NextFunction) {
  const status = err.statusCode ?? err.status ?? 500;
  const code = err.code ?? 'INTERNAL_ERROR';
  const rawMessage = err.message && typeof err.message === 'string' ? err.message : '';

  if (status >= 500 || isTechnicalError(rawMessage)) {
    console.error('[Auth]', code, rawMessage, err.stack || '');
    res.status(status >= 400 && status < 500 ? status : 500).json({
      success: false,
      code: 'SERVICE_ERROR',
      message: SAFE_USER_MESSAGE,
    });
    return;
  }

  res.status(status).json({
    success: false,
    code,
    message: rawMessage || 'Une erreur est survenue.',
  });
}
