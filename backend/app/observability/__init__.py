"""
Observabilidade: logging estruturado, correlação, privacidade e healthchecks.

Pacote central compartilhado pela API (app.main) e pelo worker (run_worker),
responsável por configurar o pipeline de logs, propagar request_id/operation_id,
aplicar redaction e manter o heartbeat do worker.
"""
