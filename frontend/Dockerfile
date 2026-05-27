# LUIGGI HOME ERP v4.0 - Build 20260527
FROM node:18-alpine AS luiggi-builder-v4b
WORKDIR /app

# Instalar dependencias
COPY package.json yarn.lock ./
RUN yarn install --network-timeout 600000 --ignore-engines --no-lockfile

# Compilar
COPY . .
ARG REACT_APP_BACKEND_URL
ENV REACT_APP_BACKEND_URL=$REACT_APP_BACKEND_URL
ENV NODE_OPTIONS=--openssl-legacy-provider
ENV CI=false
ENV GENERATE_SOURCEMAP=false
RUN yarn build

FROM node:18-alpine AS luiggi-runner-v4b
RUN npm install -g serve
WORKDIR /app
COPY --from=luiggi-builder-v4b /app/build ./build
EXPOSE 8080
CMD ["serve", "-s", "build", "-l", "8080"]
