"""
Настройка HTTP-методов проверки liveness и readiness для интеграции с k8s.

В списки checks можно добавлять проверку различных внешних системы таких как:
PostgreSQL (PostgreSqlCheck), RedisCheck (RedisCheck) и т.д.
"""

from fastapi_healthchecks.api.router import HealthcheckRouter, Probe

healthcheck_router = HealthcheckRouter(
    Probe(
        name='readiness',
        checks=[],
    ),
    Probe(
        name='liveness',
        checks=[],
    ),
)
