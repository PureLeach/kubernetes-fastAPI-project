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
