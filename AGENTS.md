# AGENTS.md - Diretrizes para o Google Jules e Agentes Autônomos

Bem-vindo ao repositório **Workana Accelerator** (`EpicFailDev/Workana`).
Este arquivo define a arquitetura, regras de codificação e comandos de verificação que o **Google Jules** e outros agentes autônomos DEVEM seguir ao executar tarefas, criar branches ou abrir Pull Requests neste repositório.

---

## 1. Visão Geral da Arquitetura

O projeto é um monorepo fullstack estruturado em:

* **Backend (`backend/`)**:
  - Framework: **FastAPI** (Python 3.11+).
  - ORM / Banco: **SQLAlchemy 2.0** assíncrono + **PostgreSQL / Supabase**.
  - Automação & Scraping: **Playwright** com rotação de fingerprints (`app/automation/`).
  - Agente de IA: Integração com **Google Gemini** para análise e geração de propostas (`app/services/proposal_agent.py`).
  - Linters / Testes: **Ruff** (format e check) e **Pytest**.

* **Frontend (`frontend/`)**:
  - Framework: **React 18** + **Vite** + **TypeScript**.
  - UI & Estilização: **Tailwind CSS**, Radix UI, Lucide Icons.
  - Estado & Roteamento: React Router DOM, React Query / Context API.
  - Linters / Testes: **ESLint**, **Prettier**, **Vitest**.

* **Supabase (`supabase/`)**:
  - Migrações SQL e políticas de segurança RLS (Row Level Security).

---

## 2. Comandos Obrigatórios de Verificação no Sandbox do Jules

O Jules roda suas alterações em um container isolado. Antes de submeter qualquer Pull Request, o Jules **DEVE** executar e passar com sucesso em:

### Comandos da Raiz do Projeto:
```bash
# Executar todos os testes (Frontend + Backend)
npm run test:all

# Verificar linters estáticos
npm run lint:all

# Checar formatação de código
npm run format:check

# Validação estrita de tipos do TypeScript
npm run typecheck
```

### Comandos Específicos por Módulo:
* **Backend**:
  ```bash
  cd backend
  python -m ruff format --check .
  python -m ruff check .
  python -m pytest
  ```
* **Frontend**:
  ```bash
  cd frontend
  npm run format:check
  npm run lint
  npm run test
  npm run build
  ```

---

## 3. Padrões de Código e Regras Inegociáveis

1. **Segurança e Credenciais (CRÍTICO)**:
   - **NUNCA** commite chaves de API, senhas, tokens de sessão ou segredos.
   - **NUNCA** modifique nem commite os arquivos `workana_storage_state.json` ou `.env`.
   - Utilize variáveis de ambiente acessadas de forma segura e com fallbacks em mocks quando rodando testes.

2. **Backend (Python / FastAPI)**:
   - Tipagem estrita com **Pydantic v2** para todos os schemas de entrada e saída.
   - Use consultas assíncronas no SQLAlchemy (`select`, `execute`). Não faça queries bloqueantes síncronas.
   - Todo novo endpoint deve ser registrado no router apropriado sob `/api/v1/`.
   - Adicione testes unitários em `backend/tests/` para qualquer nova função de serviço ou rota criada.

3. **Frontend (React / TypeScript)**:
   - TypeScript estrito (`strict: true`). **Proibido usar `any`** sem justificativa explícita.
   - Mantenha componentes modulares em `frontend/src/components/`.
   - Não quebre o build do Vite (`npm run build`).

4. **Padrão de Commits**:
   - Siga **Conventional Commits**:
     - `feat(scope): ...`
     - `fix(scope): ...`
     - `test(scope): ...`
     - `refactor(scope): ...`
     - `docs(scope): ...`

5. **Testes Regressivos**:
   - Sempre que o Jules corrigir um bug, um novo caso de teste em Pytest ou Vitest DEVE ser adicionado para comprovar a correção e prevenir regressões futuras.

---

## 4. Comunicação Natural, Decisões Autônomas e Modo Ágil

1. **Comunicação em Linguagem Natural/Leiga**:
   - O usuário pode se comunicar de forma simples e cotidiana, sem jargões de programação.
   - Interprete a intenção funcional do pedido sem exigir que o usuário especifique termos técnicos, tipos ou arquiteturas.

2. **Autonomia Técnica Total**:
   - Tome as decisões de implementação (estruturação de código, bibliotecas recomendadas, tipagem, estilização) com base nas melhores práticas do projeto e da indústria.
   - Evite perguntas de micro-decisões técnicas (ex: *"devemos usar Context ou Zustand?"*). Tome a decisão recomendada de forma autônoma e execute.

3. **Roteamento Inteligente e Ativação de Skills**:
   - Ative e aplique automaticamente as skills relevantes instaladas em `.agents/skills/` (ex: `intelligent-routing`, `frontend-design`, `systematic-debugging`, `tailwind-patterns`, `python-patterns`, `webapp-testing`) sem exigir comandos manuais ou menções explícitas do usuário.

4. **Verificação Proativa**:
   - Sempre execute a checagem e os testes necessários para garantir que nada foi quebrado antes de dar a tarefa como concluída.

5. **Explicações Claras e Humanas**:
   - Ao responder, explique o que foi feito em português claro, direto e sem jargões desnecessários, focando no resultado prático para o usuário.
