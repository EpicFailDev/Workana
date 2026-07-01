# 🚀 Workana Accelerator

**Sistema inteligente e containerizado de automação para busca e envio de propostas no Workana**

Este projeto foi completamente modernizado para rodar em produção de forma profissional em uma VPS (Virtual Private Server) usando **Docker Compose**, **Caddy** (com SSL/HTTPS automático) e o **Supabase** (PostgreSQL e Auth) na nuvem. O banco de dados SQLite local foi totalmente removido do runtime para garantir integridade transacional e isolamento multitenant (RLS).

---

## 📋 Índice

- [🛠️ Stack Tecnológica](#️-stack-tecnológica)
- [⚙️ Requisitos e Configuração](#️-requisitos-e-configuração)
- [▶️ Comandos de Desenvolvimento Local](#️-comandos-de-desenvolvimento-local)
- [🐳 Execução Local Completa com Docker](#-execução-local-completa-com-docker)
- [🖥️ Preparação da VPS Ubuntu LTS](#️-preparação-da-vps-ubuntu-lts)
- [🚀 Comandos de Deploy, Atualização e Rollback](#-comandos-de-deploy-atualização-e-rollback)
- [📊 Diagnóstico e Logs](#-diagnóstico-e-logs)
- [⚠️ Boas Práticas e Segurança](#️-boas-práticas-e-segurança)

---

## 🛠️ Stack Tecnológica

### Backend (Processos Separados)
* **FastAPI (API REST)**: Processa requisições HTTP, valida JWTs locais emitidos pelo Supabase Auth (via JWKS) e propaga o ID do usuário autenticado no contexto da transação SQL.
* **Worker (Automação/Playwright/APScheduler)**: Roda buscas agendadas robustas em background, gerencia anti-ban por usuário, gera propostas automáticas via IA (Gemini API) e envia para o Workana usando Playwright.
* **SQLAlchemy & asyncpg**: Pool de conexões altamente resiliente conectado ao Supabase com validação de saúde das conexões (`pool_pre_ping`).
* **PostgreSQL Advisory Locks**: Impede execuções concorrentes do mesmo job agendado entre múltiplas instâncias de workers.

### Frontend
* **React, Vite & TypeScript**: Interface SPA de alta performance integrada ao Supabase Auth e consumindo a API REST do backend via caminhos relativos em produção.

### Proxy & Infraestrutura
* **Caddy**: Servidor web de borda com geração automática de certificados SSL (HTTPS gratuito por Let's Encrypt/ZeroSSL), encaminhando requisições `/api/*` para o backend e demais caminhos para o frontend estático.
* **Nginx (Frontend Container)**: Servidor web minimalista embarcado no container do frontend para entrega eficiente de arquivos estáticos com cache de longa duração e SPA fallback configurado.

---

## ⚙️ Requisitos e Configuração

Certifique-se de ter instalado localmente para desenvolvimento:
* **Python 3.10+** (com `pip` e `venv`)
* **Node.js 18+** (com `npm`)
* **Docker Engine** e **Docker Compose Plugin** (para execução em containers)

### Configurando o arquivo `.env`
Copie o template `.env.example` da raiz e preencha as variáveis de ambiente necessárias:
```bash
cp .env.example .env
```
> [!IMPORTANT]
> Em produção, certifique-se de definir `DEBUG=false` e definir senhas seguras para `SECRET_KEY` e `ENCRYPTION_KEY`. A aplicação rejeitará secrets inseguros e travará a inicialização caso detecte credenciais padrões em modo de produção.

---

## ▶️ Comandos de Desenvolvimento Local

Para rodar os serviços nativamente de forma rápida durante o desenvolvimento:

### 🐍 Backend & Worker (Nativo)

1. Entre no diretório `backend` e configure o ambiente virtual:
   ```bash
   cd backend
   python -m venv venv
   # No Windows (PowerShell):
   .\venv\Scripts\activate
   # No Linux/macOS:
   source venv/bin/activate
   ```
2. Instale as dependências e o navegador do Playwright:
   ```bash
   pip install -r requirements.txt
   playwright install chromium
   ```
3. Copie o arquivo `.env` para a pasta do backend:
   ```bash
   cp ../.env .env
   ```
4. **Executar a API HTTP**:
   ```bash
   python run.py
   ```
   *(A API rodará na porta `8000`, expondo Swagger local em `http://localhost:8000/docs`)*

5. **Executar o Worker de automação (em outro terminal)**:
   ```bash
   python run_worker.py
   ```

### ⚛️ Frontend (Nativo)

1. Entre no diretório `frontend`, instale as dependências e inicie o Vite:
   ```bash
   cd frontend
   cp ../.env .env
   npm install
   npm run dev
   ```
   *(O frontend rodará na porta `8080` e utilizará o proxy do Vite para encaminhar requisições `/api` para `http://localhost:8000`)*

---

## 🐳 Execução Local Completa com Docker

Para simular o ambiente de produção completo em sua máquina local usando Docker Compose:

1. Suba todos os containers compilando as imagens:
   ```bash
   docker compose up --build -d
   ```
2. Isso iniciará:
   * `frontend` em rede interna (porta 80)
   * `api` em rede interna (porta 8000)
   * `worker` rodando o scheduler e Playwright em rede interna
   * `caddy` exposto nas portas locais **80** e **443**
3. Acesse `http://localhost` no seu navegador. O Caddy roteará as requisições `/api` para o container backend e servirá o frontend SPA estaticamente nos demais caminhos.

---

## 🖥️ Preparação da VPS Ubuntu LTS

Recomendações detalhadas para configurar uma VPS limpa (Ubuntu 22.04 LTS AMD64) antes de realizar o deploy:

### 1. Atualizar o Sistema e Instalar o Docker
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y curl git apt-transport-https ca-certificates gnupg lsb-release

# Adicionar repositório oficial do Docker
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/whitelist.d/docker.list > /dev/null

sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
sudo systemctl enable docker --now
```

### 2. Configurar Firewall (UFW)
```bash
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow http
sudo ufw allow https
sudo ufw enable
```

### 3. Configurar Swap (Recomendado para servidores de 1GB/2GB de RAM)
O Playwright e as buscas na web podem consumir picos de memória. Crie um arquivo swap de 2GB:
```bash
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

### 4. Acesso SSH por Chave Criptográfica
Evite logins por senha na VPS. Adicione sua chave pública no arquivo `~/.ssh/authorized_keys` da VPS e desative o login por senha em `/etc/ssh/sshd_config` (`PasswordAuthentication no`).

---

## 🚀 Comandos de Deploy, Atualização e Rollback

O fluxo de CI/CD pelo GitHub Actions automatiza o empacotamento em imagens Docker no **GitHub Container Registry (GHCR)** e executa os passos de deploy SSH na VPS de forma segura.

### 📌 Deploy Inicial e Configuração na VPS

1. Conecte-se na VPS e crie a pasta do projeto:
   ```bash
   mkdir -p /app/workana && cd /app/workana
   ```
2. Crie o arquivo `.env` na VPS contendo as chaves de produção corretas.
3. Copie o arquivo `Caddyfile` e `compose.yaml` do Git para a VPS.
4. Execute as migrations administrativas para inicializar o banco do Supabase:
   ```bash
   # Utilizando a CLI do Supabase local com a string administrativa do banco:
   supabase db push --db-url "postgresql://postgres.cztwxtsuewwacjcgajjz:[SENHA]@aws-1-sa-east-1.pooler.supabase.com:5432/postgres"
   ```
5. Suba os containers na VPS:
   ```bash
   docker compose pull
   docker compose up -d
   ```

### 🔄 Atualização em Produção (Sem Downtime Significativo)

Durante novos commits na branch `main`, a pipeline atualiza a VPS automaticamente:
1. Compila as imagens Docker marcadas com a tag do commit (ex: `sha-abcdef`).
2. Faz o push para o GHCR.
3. Conecta na VPS por SSH, atualiza a tag do container no `.env` da VPS.
4. Roda as migrations do Supabase (com a conexão administrativa de migrations).
5. Substitui os containers de forma segura:
   ```bash
   docker compose pull
   docker compose up -d --remove-orphans
   ```

### ⏪ Rollback para a Versão Anterior

Se a atualização apresentar erros críticos:
1. Obtenha a tag anterior bem-sucedida (ex: `v1.0.0` ou o hash do commit anterior).
2. Na VPS, atualize a tag da imagem no arquivo `.env`:
   ```bash
   sed -i 's/TAG_IMAGEM=.*/TAG_IMAGEM=hash_anterior/' .env
   ```
3. Aplique o rollback nos containers:
   ```bash
   docker compose up -d --force-recreate
   ```
4. Se necessário, reverta a migration no banco do Supabase.

---

## 📊 Diagnóstico e Logs

Comandos essenciais para depuração e acompanhamento da aplicação na VPS:

### Visualizar Logs em Tempo Real
```bash
# Todos os serviços
docker compose logs -f

# Apenas o Worker de automação
docker compose logs -f worker

# Apenas a API HTTP
docker compose logs -f api

# Logs de acesso e HTTPS do Caddy
docker compose logs -f caddy
```

### Verificar Saúde dos Containers
```bash
docker compose ps
```

### Reiniciar Serviços Individuais
```bash
docker compose restart worker
```

---

## ⚠️ Boas Práticas e Segurança

* **Privilégios Mínimos**: Os containers `api` e `worker` utilizam credenciais do banco com papéis restritos (`api_role` e `worker_role`), sem permissões administrativas de DDL (como criar ou dropar tabelas).
* **Row Level Security (RLS)**: Todas as tabelas públicas no Supabase têm RLS ativo. O backend valida a assinatura do token JWT e propaga o ID do usuário no escopo de cada transação, garantindo que nenhum usuário acesse dados de terceiros, mesmo efetuando requisições diretas na API do banco.
* **Secrets Seguros**: Nunca armazene chaves `SECRET_KEY`, `ENCRYPTION_KEY`, senhas de banco ou logins do Workana no repositório Git. Use exclusivamente o GitHub Secrets (para CI/CD) e o arquivo `.env` local da VPS (com permissão `chmod 600`).
