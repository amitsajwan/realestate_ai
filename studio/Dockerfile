# Studio (/studio and /join): its own image, built and deployed apart from the public site (frontend/).
# Build context: studio/, plus shared/ as the named context 'shared' (docker-compose additional_contexts, images.yml build-contexts).
FROM node:22-alpine AS base

FROM base AS deps
RUN apk add --no-cache libc6-compat
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
# tsconfig @shared/* = ../shared/*
COPY --from=shared . /shared

# baked into the client bundle at build time (Next.js NEXT_PUBLIC_*); the same values as the site's image
ARG NEXT_PUBLIC_BUSINESS_NAME="Avasetu"
ARG NEXT_PUBLIC_SITE_URL=
ENV NEXT_PUBLIC_BUSINESS_NAME=$NEXT_PUBLIC_BUSINESS_NAME \
    NEXT_PUBLIC_SITE_URL=$NEXT_PUBLIC_SITE_URL

RUN npm run build

FROM base AS runner
WORKDIR /app
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
RUN addgroup --system --gid 1001 nodejs && adduser --system --uid 1001 nextjs
# public/studio/sw.js: the phone alerts' service worker
COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static
USER nextjs
EXPOSE 3000
ENV PORT=3000
ENV HOSTNAME="0.0.0.0"
CMD ["node", "server.js"]
