# 🚀 Workana Automation

<div align="center">

![Logo](https://img.shields.io/badge/🤖-Workana_Automation-6366f1?style=for-the-badge)

**Sistema inteligente de automação para busca e envio de propostas no Workana**

[![Status](https://img.shields.io/badge/status-em%20desenvolvimento-yellow?style=flat-square)](/)
[![Python](https://img.shields.io/badge/python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![Next.js](https://img.shields.io/badge/next.js-14-000000?style=flat-square&logo=next.js&logoColor=white)](https://nextjs.org)
[![FastAPI](https://img.shields.io/badge/fastapi-0.109-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Playwright](https://img.shields.io/badge/playwright-1.41-2EAD33?style=flat-square&logo=playwright&logoColor=white)](https://playwright.dev)

</div>

---

## 📋 Índice

- [✨ Funcionalidades](#-funcionalidades)
- [🛠️ Stack Tecnológica](#️-stack-tecnológica)
- [📁 Estrutura do Projeto](#-estrutura-do-projeto)
- [🚀 Instalação](#-instalação)
- [▶️ Executar](#️-executar)
- [📖 Como Usar](#-como-usar)
- [🔌 API Endpoints](#-api-endpoints)
- [📝 Variáveis de Template](#-variáveis-de-template)
- [⚙️ Configurações](#️-configurações)
- [⚠️ Avisos Importantes](#️-avisos-importantes)

---

## ✨ Funcionalidades

| Funcionalidade | Descrição |
|----------------|-----------|
| 🔐 **Login Automático** | Acesse sua conta Workana automaticamente |
| 🔍 **Busca Inteligente** | Filtros avançados por categoria, orçamento, skills |
| 📝 **Templates Dinâmicos** | Propostas personalizáveis com variáveis |
| 📊 **Dashboard** | Estatísticas e métricas em tempo real |
| 📜 **Histórico** | Acompanhe todas as propostas enviadas |
| 💾 **Filtros Salvos** | Reutilize suas buscas favoritas |
| ⚙️ **Anti-Detecção** | Delays configuráveis para simular comportamento humano |
| 🔒 **Segurança** | Credenciais armazenadas com criptografia Fernet |

---

## 🛠️ Stack Tecnológica

### Backend
| Tecnologia | Versão | Uso |
|------------|--------|-----|
| **Python** | 3.10+ | Runtime principal |
| **FastAPI** | 0.109 | API REST de alta performance |
| **Playwright** | 1.41 | Automação de navegador |
| **SQLAlchemy** | 2.0 | ORM para banco de dados |
| **SQLite** | - | Banco de dados local |
| **Pydantic** | 2.5 | Validação de dados |
| **Loguru** | 0.7 | Logging estruturado |

### Frontend
| Tecnologia | Versão | Uso |
|------------|--------|-----|
| **Next.js** | 14 | Framework React |
| **TypeScript** | 5.x | Tipagem estática |
| **CSS Modules** | - | Estilização modular |
| **React** | 18 | Biblioteca de UI |

---

## 📁 Estrutura do Projeto

```
workana-automation/
│
├── 📂 backend/                    # Servidor Python
│   ├── 📂 app/
│   │   ├── 📂 api/
│   │   │   ├── __init__.py
│   │   │   ├── routes.py          # 15+ endpoints REST
│   │   │   └── schemas.py         # Modelos Pydantic
│   │   │
│   │   ├── 📂 automation/
│   │   │   ├── __init__.py
│   │   │   └── browser.py         # Automação Playwright
│   │   │
│   │   ├── 📂 database/
│   │   │   ├── __init__.py
│   │   │   ├── models.py          # Modelos SQLAlchemy
│   │   │   └── crud.py            # Operações CRUD
│   │   │
│   │   ├── __init__.py
│   │   ├── config.py              # Configurações centralizadas
│   │   └── main.py                # Aplicação FastAPI
│   │
│   ├── .env.example               # Template de variáveis
│   └── requirements.txt           # Dependências Python
│
├── 📂 frontend/                   # Interface Next.js
│   ├── 📂 src/
│   │   ├── 📂 app/
│   │   │   ├── layout.tsx         # Layout principal
│   │   │   ├── page.tsx           # Dashboard
│   │   │   ├── globals.css        # Design System
│   │   │   ├── 📂 projects/       # Busca de projetos
│   │   │   ├── 📂 templates/      # Templates de proposta
│   │   │   ├── 📂 filters/        # Filtros salvos
│   │   │   ├── 📂 history/        # Histórico
│   │   │   └── 📂 settings/       # Configurações
│   │   │
│   │   ├── 📂 components/
│   │   │   ├── Sidebar.tsx
│   │   │   └── Sidebar.module.css
│   │   │
│   │   └── 📂 services/
│   │       └── api.ts             # Cliente API
│   │
│   └── package.json
│
└── README.md                      # Este arquivo
```

---

## 🚀 Instalação

### Pré-requisitos

Certifique-se de ter instalado:
- ✅ **Python 3.10+** ([Download](https://python.org/downloads))
- ✅ **Node.js 18+** ([Download](https://nodejs.org))
- ✅ **Git** ([Download](https://git-scm.com))

---

### ⚡ Instalação Rápida (1 Comando)

```powershell
# Clone e instale tudo automaticamente
git clone https://github.com/seu-usuario/workana-automation.git
cd workana-automation
.\setup.ps1
```

O script `setup.ps1` faz automaticamente:
- ✅ Cria ambiente virtual Python
- ✅ Instala dependências do backend
- ✅ Instala Playwright/Chromium
- ✅ Configura arquivo `.env`
- ✅ Instala dependências do frontend

---

## ▶️ Executar

### ⚡ Início Rápido (1 Comando)

```powershell
.\start.ps1
```

Este comando:
- 🐍 Inicia o Backend (FastAPI) na porta 8000
- ⚛️ Inicia o Frontend (Next.js) na porta 3000
- 🌐 Abre o navegador automaticamente

| URL | Descrição |
|-----|-----------|
| http://localhost:3000 | Interface Web |
| http://localhost:8000 | API REST |
| http://localhost:8000/docs | Documentação Swagger |

---

### 📋 Instalação Manual (Opcional)

<details>
<summary>Clique para ver os passos manuais</summary>

#### Passo 1: Configurar Backend

```powershell
# Entrar na pasta do backend
cd backend

# Criar ambiente virtual Python
python -m venv venv

# Ativar ambiente virtual (Windows PowerShell)
.\venv\Scripts\activate

# Ativar ambiente virtual (Linux/macOS)
# source venv/bin/activate

# Instalar dependências Python
pip install -r requirements.txt

# Instalar navegador Chromium para Playwright
playwright install chromium

# Criar arquivo de configuração
copy .env.example .env
```

#### Passo 2: Configurar Frontend

```powershell
# Voltar para raiz e entrar no frontend
cd ../frontend

# Instalar dependências Node.js
npm install
```

#### Iniciar Backend Manualmente

```powershell
cd backend
.\venv\Scripts\activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Iniciar Frontend Manualmente

```powershell
cd frontend
npm run dev
```

</details>

---

## 📖 Como Usar

### 1️⃣ Configurar Credenciais
Acesse **Configurações** e insira seu email e senha do Workana. As credenciais são armazenadas localmente com criptografia.

### 2️⃣ Fazer Login
No **Dashboard**, clique em "Fazer Login" para conectar ao Workana.

### 3️⃣ Criar Templates
Em **Templates**, crie modelos de proposta com variáveis dinâmicas que serão substituídas automaticamente.

### 4️⃣ Buscar Projetos
Use a página **Projetos** para pesquisar com filtros por categoria, orçamento, skills, etc.

### 5️⃣ Enviar Propostas
Selecione um projeto e envie sua proposta usando um template ou mensagem personalizada.

### 6️⃣ Acompanhar
Veja o status das suas propostas no **Histórico**.

---

## 🔌 API Endpoints

### Autenticação e Automação
| Método | Endpoint | Descrição |
|--------|----------|-----------|
| `POST` | `/api/credentials` | Salvar credenciais |
| `GET` | `/api/credentials/status` | Verificar se configurado |
| `POST` | `/api/automation/login` | Fazer login no Workana |
| `POST` | `/api/automation/logout` | Desconectar |
| `GET` | `/api/automation/status` | Status da automação |

### Projetos
| Método | Endpoint | Descrição |
|--------|----------|-----------|
| `POST` | `/api/projects/search` | Buscar projetos com filtros |
| `GET` | `/api/projects/{id}` | Detalhes de um projeto |

### Templates
| Método | Endpoint | Descrição |
|--------|----------|-----------|
| `GET` | `/api/templates` | Listar templates |
| `POST` | `/api/templates` | Criar template |
| `PUT` | `/api/templates/{id}` | Atualizar template |
| `DELETE` | `/api/templates/{id}` | Remover template |

### Propostas
| Método | Endpoint | Descrição |
|--------|----------|-----------|
| `POST` | `/api/proposals/send` | Enviar proposta |
| `GET` | `/api/proposals/history` | Histórico de propostas |

### Dashboard
| Método | Endpoint | Descrição |
|--------|----------|-----------|
| `GET` | `/api/dashboard/stats` | Estatísticas gerais |

### Projetos Salvos
| Método | Endpoint | Descrição |
|--------|----------|-----------|
| `GET` | `/api/saved-projects` | Listar projetos salvos |
| `GET` | `/api/saved-projects/{id}` | Detalhes de um projeto salvo |
| `POST` | `/api/saved-projects` | Salvar um projeto |
| `POST` | `/api/saved-projects/{id}/favorite` | Favoritar/desfavoritar |
| `POST` | `/api/saved-projects/{id}/applied` | Marcar como aplicado |
| `POST` | `/api/saved-projects/{id}/ignore` | Ignorar projeto |
| `PUT` | `/api/saved-projects/{id}/notes` | Atualizar notas |

### Logs de Atividade
| Método | Endpoint | Descrição |
|--------|----------|-----------|
| `GET` | `/api/logs` | Listar logs de atividade |
| `POST` | `/api/logs` | Criar log manual |

### Estatísticas
| Método | Endpoint | Descrição |
|--------|----------|-----------|
| `GET` | `/api/statistics` | Estatísticas dos últimos N dias |
| `GET` | `/api/statistics/summary` | Resumo (hoje/semana/mês) |

### Clientes Bloqueados
| Método | Endpoint | Descrição |
|--------|----------|-----------|
| `GET` | `/api/blacklist` | Listar clientes bloqueados |
| `POST` | `/api/blacklist` | Adicionar à lista negra |
| `DELETE` | `/api/blacklist/{id}` | Remover da lista negra |
| `GET` | `/api/blacklist/check/{nome}` | Verificar se está bloqueado |

### Sistema Anti-Ban 🛡️
| Método | Endpoint | Descrição |
|--------|----------|-----------|
| `GET` | `/api/antiban/status` | Status atual do sistema |
| `GET` | `/api/antiban/config` | Configuração atual |
| `PUT` | `/api/antiban/config` | Atualizar configuração |
| `GET` | `/api/antiban/can-send-proposal` | Verificar se pode enviar |
| `GET` | `/api/antiban/can-search` | Verificar se pode buscar |
| `GET` | `/api/antiban/working-hours` | Horário de operação |

---

## 🛡️ Sistema Anti-Ban

O sistema inclui proteção avançada para evitar detecção e banimento:

### Proteções Implementadas

| Proteção | Descrição |
|----------|-----------|
| 🕐 **Delays Aleatórios** | 1.5s - 4s entre ações (variável) |
| 📊 **Limites de Ações** | Máx. 8 propostas/dia, 3/hora |
| ⏰ **Horário de Operação** | Apenas das 8h às 22h |
| 🖱️ **Simulação Humana** | Movimentos de mouse, scroll aleatório |
| 🔄 **Fingerprinting** | User-agents e resoluções aleatórias |
| ⏸️ **Pausas Obrigatórias** | 10-30 min entre propostas |
| 🚫 **Anti-Detecção** | Remove indicadores de automação |

### Configurações Padrão

```json
{
  "max_proposals_per_day": 8,
  "max_proposals_per_hour": 3,
  "max_searches_per_hour": 10,
  "min_pause_between_proposals_minutes": 10,
  "max_pause_between_proposals_minutes": 30,
  "working_hours_start": 8,
  "working_hours_end": 22
}
```

### Como Configurar

Via API:
```bash
curl -X PUT http://localhost:8000/api/antiban/config \
  -H "Content-Type: application/json" \
  -d '{"max_proposals_per_day": 5, "min_pause_between_proposals_minutes": 15}'
```

---

## 📝 Variáveis de Template

Use estas variáveis nos seus templates de proposta. Elas serão substituídas automaticamente:

| Variável | Descrição | Exemplo |
|----------|-----------|---------|
| `{nome_cliente}` | Nome do cliente | João Silva |
| `{titulo_projeto}` | Título do projeto | App Mobile React Native |
| `{valor}` | Valor proposto | 5.000 |
| `{prazo}` | Prazo em dias | 30 |
| `{anos_experiencia}` | Sua experiência | 5 |
| `{data_atual}` | Data de envio | 24/12/2024 |

### Exemplo de Template

```text
Olá {nome_cliente}!

Vi o seu projeto "{titulo_projeto}" e fiquei muito interessado.

Tenho {anos_experiencia} anos de experiência na área e posso 
entregar um trabalho de qualidade.

📌 Minha proposta:
• Valor: R$ {valor}
• Prazo: {prazo} dias
• Entregas parciais para acompanhamento

Podemos conversar para discutir os detalhes?

Atenciosamente!
```

---

## ⚙️ Configurações

### Variáveis de Ambiente (.env)

```env
# Credenciais Workana (opcional, pode configurar pela interface)
WORKANA_EMAIL=seu@email.com
WORKANA_PASSWORD=sua_senha

# Segurança
SECRET_KEY=sua_chave_secreta_aqui
ENCRYPTION_KEY=chave_para_criptografia

# API
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=true

# Automação
HEADLESS=true
SLOW_MO=100
MAX_PROPOSALS_PER_DAY=10
DELAY_BETWEEN_ACTIONS_MS=2000
```

### Configurações Recomendadas

| Configuração | Valor Recomendado | Descrição |
|--------------|-------------------|-----------|
| **Delay** | 2000-3000ms | Tempo entre ações para parecer humano |
| **Limite Diário** | 5-10 | Propostas por dia |
| **Modo Headless** | Ativado | Navegador invisível |
| **Slow Motion** | 100ms | Velocidade de digitação |

---

## ⚠️ Avisos Importantes

> [!WARNING]
> **Termos de Uso do Workana**
> 
> O uso de automação pode violar os Termos de Serviço do Workana. Use esta ferramenta por sua própria conta e risco. Recomendamos:
> - Usar delays realistas entre ações
> - Limitar o número de propostas diárias
> - Não executar 24/7
> - Monitorar sua conta regularmente

> [!CAUTION]
> **Risco de Suspensão**
> 
> Uso excessivo ou padrões detectáveis podem resultar em suspensão temporária ou permanente da sua conta Workana.

> [!TIP]
> **Melhores Práticas**
> 
> - Configure delays de pelo menos 2 segundos
> - Limite a 5-10 propostas por dia
> - Varie os horários de uso
> - Personalize seus templates para cada tipo de projeto

---

## 🤝 Contribuição

Contribuições são bem-vindas! Sinta-se à vontade para:

1. 🍴 Fazer fork do projeto
2. 🔧 Criar uma branch (`git checkout -b feature/nova-funcionalidade`)
3. 💾 Commit suas mudanças (`git commit -m 'Adiciona nova funcionalidade'`)
4. 📤 Push para a branch (`git push origin feature/nova-funcionalidade`)
5. 📝 Abrir um Pull Request

---

## 📄 Licença

Este projeto é para **uso pessoal e educacional**.

Não nos responsabilizamos pelo uso indevido desta ferramenta ou por qualquer consequência decorrente de seu uso.

---

<div align="center">

**Desenvolvido com ❤️ para freelancers**

⭐ Se este projeto te ajudou, deixe uma estrela!

</div>