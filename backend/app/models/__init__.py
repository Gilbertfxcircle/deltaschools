"""ORM models.

``global_models`` -> tables in ``deltaplax_global``.
``school_models``  -> per-tenant tables (schema chosen at runtime).
"""

from app.models import global_models, school_models  # noqa: F401
