"""Import all models so SQLAlchemy metadata is fully populated."""
from app.db.base import Base  # noqa: F401
from app.models.user import (  # noqa: F401
    ALL_ROLES,
    ROLE_ANALYST,
    ROLE_ORG_ADMIN,
    ROLE_PLATFORM_ADMIN,
    ROLE_SOC_MANAGER,
    ROLE_VIEWER,
    Organization,
    Role,
    User,
    UserRole,
)
from app.models.customer import (  # noqa: F401
    Asset,
    Customer,
    CustomerAIPolicy,
    CustomerAllowlist,
    KnownFalsePositive,
    ServiceAccount,
)
from app.models.alert import (  # noqa: F401
    Alert,
    Case,
    Entity,
    EnrichmentResult,
    IOC,
    NormalizedAlert,
    STATUS_CLOSED,
    STATUS_CORRELATED,
    STATUS_ENRICHED,
    STATUS_INVESTIGATED,
    STATUS_NEW,
    STATUS_PARSED,
    STATUS_REPORTED,
)
from app.models.investigation import (  # noqa: F401
    AIVerdict,
    ApprovalRequest,
    EmailDraft,
    Feedback,
    Investigation,
    Report,
    ResponseRecommendation,
    TicketNote,
)
from app.models.ai import (  # noqa: F401
    AIPromptTemplate,
    AIProviderConfig,
    AIRun,
)
from app.models.misc import (  # noqa: F401
    AuditLog,
    Integration,
    KnowledgeDocument,
    Playbook,
    VectorMemoryMetadata,
)

__all__ = ["Base"]
