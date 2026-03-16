FROM node:18-alpine as base

WORKDIR /app

# Install dependencies (including devDependencies for development)
COPY package*.json ./
RUN --mount=type=cache,target=/root/.npm \
    npm ci

# Build application
COPY . .
# Ensure public directory exists (Next.js requires it)
RUN mkdir -p public
RUN npm run build

# Production image
FROM node:18-alpine
WORKDIR /app

ENV NODE_ENV=production

# Copy built application
COPY --from=base /app/.next ./.next
COPY --from=base /app/package*.json ./
COPY --from=base /app/node_modules ./node_modules

# Copy public directory - it should exist from base stage
RUN mkdir -p ./public
COPY --from=base /app/public ./public

EXPOSE 3000

CMD ["npm", "start"]

# Development image (for docker-compose dev mode)
FROM base as development

ENV NODE_ENV=development

EXPOSE 3000

CMD ["npm", "run", "dev"]
