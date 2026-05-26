FROM node:18-alpine AS builder2026
WORKDIR /app

COPY package.json yarn.lock ./
RUN yarn install --network-timeout 600000 --ignore-engines

COPY . .
ARG REACT_APP_BACKEND_URL
ENV REACT_APP_BACKEND_URL=$REACT_APP_BACKEND_URL
ENV NODE_OPTIONS=--openssl-legacy-provider
ENV CI=false
ENV GENERATE_SOURCEMAP=false
RUN yarn build

FROM node:18-alpine AS runner2026
RUN npm install -g serve
WORKDIR /app
COPY --from=builder2026 /app/build ./build
EXPOSE 8080
CMD ["serve", "-s", "build", "-l", "8080"]
