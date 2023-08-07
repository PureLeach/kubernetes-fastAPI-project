"""
Интеграция Prometheus с FastAPI

Prometheus - это система мониторинга и алертинга, которая позволяет
собирать и анализировать метрики приложения.
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
