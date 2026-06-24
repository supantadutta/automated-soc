from app.api.routes import (
    ai_providers,
    alerts,
    allowlists,
    audit,
    auth,
    customers,
    dashboard,
    investigations,
    knowledge,
    playbooks,
    reports,
    response,
)

ALL_ROUTERS = [
    auth.router,
    customers.router,
    alerts.router,
    investigations.router,
    reports.router,
    ai_providers.router,
    dashboard.router,
    playbooks.router,
    allowlists.router,
    audit.router,
    knowledge.router,
    response.router,
]
