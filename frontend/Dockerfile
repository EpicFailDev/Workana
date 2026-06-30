# Stage 1: Build the Vite SPA
FROM node:20-alpine AS build

WORKDIR /app

# Instala dependências usando npm ci para consistência
COPY package*.json ./
RUN npm ci

# Copia os arquivos do frontend
COPY . .

# Recebe chaves públicas do Supabase necessárias durante a compilação do Vite
ARG VITE_SUPABASE_URL
ARG VITE_SUPABASE_PUBLISHABLE_KEY

ENV VITE_SUPABASE_URL=${VITE_SUPABASE_URL}
ENV VITE_SUPABASE_PUBLISHABLE_KEY=${VITE_SUPABASE_PUBLISHABLE_KEY}

# Roda o build de produção (faz type-check e gera arquivos em /app/dist)
RUN npm run build

# Stage 2: Serve static files using Nginx
FROM nginx:alpine

# Copia os arquivos estáticos compilados da etapa anterior
COPY --from=build /app/dist /usr/share/nginx/html

# Sobrescreve a configuração padrão do Nginx para suportar SPA fallback
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
