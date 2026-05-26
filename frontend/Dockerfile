FROM node:18-alpine AS build
WORKDIR /app

# Instalar dependencias primero (cache layer)
COPY package.json yarn.lock ./
RUN yarn install --network-timeout 600000

# Copiar código y compilar
COPY . .
ARG REACT_APP_BACKEND_URL
ENV REACT_APP_BACKEND_URL=$REACT_APP_BACKEND_URL
ENV NODE_OPTIONS=--openssl-legacy-provider
ENV CI=false
RUN yarn build

# Servidor de producción
FROM node:18-alpine
RUN npm install -g serve
WORKDIR /app
COPY --from=build /app/build ./build
EXPOSE 8080
CMD ["serve", "-s", "build", "-l", "8080"]
