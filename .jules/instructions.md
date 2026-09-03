# Instruções Específicas para o Google Jules

## Objetivo
O Google Jules atua como engenheiro de software assíncrono para o projeto **Workana Accelerator**.

## Passos de Execução do Sandbox
Ao receber uma tarefa:
1. **Explore**: Inspecione os arquivos relevantes descritos na tarefa ou issue.
2. **Reproduza / Crie Testes**: Se for correção de bug, adicione um teste automatizado primeiro.
3. **Implemente**: Faça mudanças pontuais e cirúrgicas sem quebrar funcionalidades existentes.
4. **Verifique no Sandbox**:
   - Backend: `cd backend && python -m ruff check . && python -m pytest`
   - Frontend: `cd frontend && npm run lint && npm run test && npm run build`
   - Ou na raiz: `npm run lint:all && npm run test:all`
5. **Finalize**: Abra o Pull Request descrevendo claramente o problema resolvido, a abordagem adotada e os testes executados.
