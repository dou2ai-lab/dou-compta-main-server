/**
 * JWT auth middleware. Attaches userId to request.
 */
import { Request, Response, NextFunction } from 'express';
import { verifyAccessToken } from '../services/authService';

export function authMiddleware(req: Request, res: Response, next: NextFunction) {
  const authHeader = req.headers.authorization;
  const token = authHeader?.startsWith('Bearer ') ? authHeader.slice(7) : null;
  if (!token) {
    return res.status(401).json({
      success: false,
      code: 'UNAUTHORIZED',
      message: 'Token manquant.',
    });
  }
  const payload = verifyAccessToken(token);
  if (!payload) {
    return res.status(401).json({
      success: false,
      code: 'INVALID_TOKEN',
      message: 'Token invalide ou expiré.',
    });
  }
  (req as any).userId = payload.sub;
  (req as any).userEmail = payload.email;
  (req as any).tenantId = payload.tenantId;
  (req as any).roles = payload.roles;
  next();
}
