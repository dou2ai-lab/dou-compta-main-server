/**
 * Express server. CORS enabled for frontend; global rate limit; auth under /api/v1/auth.
 */
import express from 'express';
import cors from 'cors';
import rateLimit from 'express-rate-limit';
import authRoutes from './routes/authRoutes';
import { errorHandler } from './middleware/errorHandler';
import { config } from './config';

const app = express();

app.use(cors({ origin: true, credentials: true }));
app.use(express.json());

const limiter = rateLimit({
  windowMs: config.rateLimit.windowMs,
  max: config.rateLimit.max,
  standardHeaders: true,
  legacyHeaders: false,
});
app.use(limiter);

app.get('/health', (_req, res) => {
  res.json({ status: 'ok', service: 'auth' });
});

app.use('/api/v1/auth', authRoutes);

app.use(errorHandler);

app.listen(config.port, () => {
  console.log(`Auth service listening on port ${config.port}`);
});
