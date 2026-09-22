# Builder stage
FROM node:18-alpine AS builder

WORKDIR /app

# Enable standalone output
ENV NEXT_PRIVATE_STANDALONE=true

ARG NEXT_PUBLIC_API_BASE_URL
ENV NEXT_PUBLIC_API_BASE_URL=$NEXT_PUBLIC_API_BASE_URL

# Read at build time by lib/site.ts for canonical/Open Graph URLs, sitemap.xml
# and robots.txt's sitemap link - same "must be a build ARG, not just a
# runtime env var" rule as INTERNAL_API_BASE_URL below. Missing this makes
# every one of those point at http://localhost:3000 in the built output,
# which is exactly the kind of thing that keeps a real site out of Google.
ARG NEXT_PUBLIC_SITE_URL
ENV NEXT_PUBLIC_SITE_URL=$NEXT_PUBLIC_SITE_URL

# Read at build time by next.config.mjs's rewrites(), which Next.js resolves
# once into .next/standalone's routing manifest - NOT re-read from the
# runtime environment. Must be passed as a build arg, not just a container
# env var, or the rewrite silently falls back to its 127.0.0.1 default.
ARG INTERNAL_API_BASE_URL
ENV INTERNAL_API_BASE_URL=$INTERNAL_API_BASE_URL

COPY package*.json ./
RUN npm ci

COPY . .

# Build the application
RUN npm run build

# Runner stage
FROM node:18-alpine AS runner

WORKDIR /app

ENV NODE_ENV=production

# Don't run as root for security
RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

# Copy essential files from builder
# We use standalone output for a much smaller image size
COPY --from=builder --chown=nextjs:nodejs /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs

EXPOSE 3000

ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

CMD ["node", "server.js"]
