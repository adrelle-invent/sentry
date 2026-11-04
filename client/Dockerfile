FROM node:22-alpine

# Enable corepack so pnpm is available
RUN corepack enable

WORKDIR /app

# Copy package manifest and pnpm lockfile explicitly
COPY package.json pnpm-lock.yaml ./

# Install dependencies with frozen lockfile for reproducible builds
RUN pnpm install --frozen-lockfile

# Copy the remaining application source code
COPY . .

CMD ["pnpm", "run", "dev"]