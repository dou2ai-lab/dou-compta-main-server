/**
 * Auth API routes. Paths match frontend: /api/v1/auth/*
 */
import { Router } from 'express';
import rateLimit from 'express-rate-limit';
import * as authController from '../controllers/authController';
import { authMiddleware } from '../middleware/authMiddleware';
import { config } from '../config';

const router = Router();

const authLimiter = rateLimit({
  windowMs: config.rateLimit.authWindowMs,
  max: config.rateLimit.authMax,
  message: { success: false, code: 'TOO_MANY_REQUESTS', message: 'Trop de tentatives. Réessayez plus tard.' },
  standardHeaders: true,
  legacyHeaders: false,
});

router.post('/signup', authLimiter, authController.signup);
router.post('/login', authLimiter, authController.login);
router.post('/logout', authController.logout);
router.post('/refresh', authController.refresh);
router.post('/forgot-password', authLimiter, authController.forgotPassword);
router.post('/reset-password', authController.resetPassword);
router.get('/me', authMiddleware, authController.me);

// OAuth / SSO (Google, Microsoft, Okta)
router.get('/oauth/:provider/start', authController.oauthStart);
router.get('/oauth/:provider/callback', authController.oauthCallback);

export default router;
