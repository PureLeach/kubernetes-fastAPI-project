"""Prometheus integration with FastAPI."""

from prometheus_fastapi_instrumentator import Instrumentator, metrics

instrumentator = Instrumentator(should_group_status_codes=True)

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
