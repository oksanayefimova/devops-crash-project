# ---------- Build stage: Node 16 ----------
FROM node:16-alpine AS build
WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci --legacy-peer-deps

COPY . .

# Backend address is baked into the bundle at build time
ARG REACT_APP_ROOT_SERVER=http://localhost:8080
ENV REACT_APP_ROOT_SERVER=$REACT_APP_ROOT_SERVER
RUN npm run build

# ---------- Runtime stage: nginx ----------
FROM nginx:1.27-alpine

COPY nginx/default.conf /etc/nginx/conf.d/default.conf
# App uses basename /dev (see package.json "homepage" and ApplicationConfig.js)
COPY --from=build /app/build /usr/share/nginx/html/dev

EXPOSE 80
