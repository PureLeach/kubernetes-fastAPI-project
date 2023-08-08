"""
Prometheus integration with FastAPI

Prometheus is a monitoring and alerting system that allows you to
collect and analyse application metrics.
"""

from prometheus_fastapi_instrumentator import Instrumentator, metrics

instrumentator = Instrumentator(should_group_status_codes=True, should_respect_env_var=True)

instrumentator.add(
    metrics.request_size(
        should_include_handler=True,
        should_include_method=False,
        should_include_status=True,
    ),
).add(
    metrics.response_size(
        should_include_handler=True,
        should_include_method=False,
        should_include_status=True,
    ),
)
