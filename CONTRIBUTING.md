# Guia de Contribuição - Workana Accelerator

Bem-vindo ao repositório do **Workana Accelerator**! Para manter a integridade, velocidade e confiabilidade da base de código, seguimos padrões estritos de engenharia similares aos de grandes empresas de tecnologia (Big Tech).

---

## 1. Convenção de Commits (Conventional Commits)

Todas as mensagens de commit devem seguir o padrão [Conventional Commits v1.0.0](https://www.conventionalcommits.org/):

```
<tipo>(<escopo opcional>): <descrição no imperativo e em minúsculas>

[corpo opcional explicando o porquê da mudança]

[rodapé opcional com referências a issues]
```

### Tipos Permitidos:
- **`feat`**: Nova funcionalidade para o usuário final.
- **`fix`**: Correção de bug.
- **`docs`**: Alterações puramente de documentação.
- **`style`**: Formatação de código (espaçamento, ponto e vírgula) sem alteração de lógica.
- **`refactor`**: Refatoração de código que não altera comportamento nem adiciona funcionalidade.
- **`test`**: Adição ou ajuste de testes automatizados (unitários ou integração).
- **`chore`**: Tarefas de manutenção, atualização de dependências ou build scripts.
- **`ci`**: Mudanças em arquivos de integração contínua (`.github/workflows`).

### Exemplos:
- `feat(projects): add bulk export to csv button`
- `fix(auth): handle expired supabase jwt refresh tokens`
- `refactor(scraper): extract antiban fingerprint rotation into dedicated class`
- `test(backend): add unit tests for investment currency conversion`

---

## 2. Fluxo de Trabalho e Branches (Trunk-Based)

1. Crie uma branch a partir da `main`:
   ```bash
   git checkout -b feat/nome-da-feature
   # ou
   git checkout -b fix/nome-do-bug
   ```
2. Realize mudanças pequenas, atômicas e testadas.
3. Antes de abrir o Pull Request, execute a validação completa:
   ```bash
   # Formatar todo o código
   npm run format:all

   # Rodar linters estáticos
   npm run lint:all

   # Executar suíte completa de testes
   npm run test:all
   ```
4. Abra um Pull Request contra a branch `main`. A esteira de CI do GitHub Actions executará os mesmos testes e bloqueará merges se houver regressões.

---

## 3. Guia Rápido de Comandos

O repositório possui uma interface de desenvolvimento unificada a partir da raiz:

| Ação | Comando Raiz | Descrição |
| :--- | :--- | :--- |
| **Iniciar Modo Dev** | `npm run dev:frontend` | Inicia o servidor Vite na porta 5173 |
| **Iniciar API** | `npm run dev:backend` | Inicia o FastAPI com reload na porta 8000 |
| **Formatar Tudo** | `npm run format:all` | Executa Prettier no frontend e Ruff no backend |
| **Verificar Formato**| `npm run format:check` | Checa se há arquivos fora do padrão sem modificá-los |
| **Linters** | `npm run lint:all` | Roda ESLint no frontend e Ruff Check no backend |
| **Testes Gerais** | `npm run test:all` | Executa testes do Vitest e Pytest |
| **Checagem de Tipos**| `npm run typecheck` | Executa validação de tipos do TypeScript (`tsc -b`) |

---

## 4. Padrões de Código

### TypeScript & React (Frontend)
- Utilize TypeScript estrito (`strict: true`).
- Evite o uso de `any`; crie interfaces ou types dedicados.
- Prefira componentes funcionais com hooks.
- Mantenha o código formatado via Prettier (`.prettierrc`).

### Python & FastAPI (Backend)
- Tipagem estrita com Pydantic v2 para requests e responses de APIs.
- Padrão PEP 8 formatado e validado via Ruff (`pyproject.toml`).
- Use consultas assíncronas com SQLAlchemy (`select`, `execute`).
- Nunca commite segredos ou tokens de sessão (`.env` ou `workana_storage_state.json`).
