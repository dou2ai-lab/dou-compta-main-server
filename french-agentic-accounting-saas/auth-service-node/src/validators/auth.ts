/**
 * Request validation with Zod.
 * French-friendly error messages; strong password rules (EU recommendations).
 */
import { z } from 'zod';

const emailSchema = z
  .string()
  .min(1, 'L’email est requis.')
  .email('Veuillez entrer une adresse email valide.');

// Min 8 chars, at least one letter and one number (common EU baseline)
const passwordSchema = z
  .string()
  .min(8, 'Le mot de passe doit contenir au moins 8 caractères.')
  .regex(/[A-Za-z]/, 'Le mot de passe doit contenir au moins une lettre.')
  .regex(/\d/, 'Le mot de passe doit contenir au moins un chiffre.');

export const signupSchema = z.object({
  body: z.object({
    email: emailSchema,
    password: passwordSchema,
    first_name: z.string().max(100).optional(),
    last_name: z.string().max(100).optional(),
  }),
});

export const loginSchema = z.object({
  body: z.object({
    email: emailSchema,
    password: z.string().min(1, 'Le mot de passe est requis.'),
  }),
});

export const refreshSchema = z.object({
  body: z.object({
    refresh_token: z.string().min(1, 'Le jeton de rafraîchissement est requis.'),
  }),
});

export const forgotPasswordSchema = z.object({
  body: z.object({
    email: emailSchema,
  }),
});

export const resetPasswordSchema = z.object({
  body: z.object({
    token: z.string().min(1, 'Le lien de réinitialisation est invalide ou expiré.'),
    new_password: passwordSchema,
  }),
});

export type SignupBody = z.infer<typeof signupSchema>['body'];
export type LoginBody = z.infer<typeof loginSchema>['body'];
export type RefreshBody = z.infer<typeof refreshSchema>['body'];
export type ForgotPasswordBody = z.infer<typeof forgotPasswordSchema>['body'];
export type ResetPasswordBody = z.infer<typeof resetPasswordSchema>['body'];
