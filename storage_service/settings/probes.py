"""
Configuring HTTP liveness and readiness validation methods for integration with k8s.

To list you can add checking of various external systems such as:
PostgreSQL (PostgreSqlCheck), RedisCheck (RedisCheck), etc.
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
