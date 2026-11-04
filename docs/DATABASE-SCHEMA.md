# Database Schema & Migration Standards

This document outlines the architectural standards for data modeling using asynchronous SQLAlchemy, database migrations via Alembic, and indexing strategies for the **AD. Sentry** platform.

---

## 1. Asynchronous SQLAlchemy Models & Conventions

To support high-throughput, non-blocking operations in FastAPI, all database interactions utilize SQLAlchemy's `AsyncSession` and asynchronous engine configuration (`server/core/database.py`).

### Model Anatomy & Standards

- **Location:** Database models live strictly inside their respective vertical domain modules (`server/modules/<domain>/models.py`).
- **Base Class:** All models inherit from a shared declarative base that includes standard audit columns.
- **Primary Keys:** Standardize on UUIDv4 or auto-incrementing BigInts depending on domain distribution needs (defaulting to UUIDv4 for distributed entity safety).
- **Audit Mixin:** Every table should include immutable creation timestamps and update tracking:

```python
created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
```

---

## 2. Alembic Migration Standards

Database schema evolutions are strictly managed through Alembic migrations located in `server/alembic/`. Direct schema modifications against production or staging databases are prohibited.

### Migration Workflow Rules

1. **Autogenerate with Review:** When modifying models in `models.py`, generate the migration script using:

```bash
alembic revision --autogenerate -m "describe_change_here"
```

2. **Mandatory Inspection:** Always review the generated Alembic script before committing. Ensure data-loss operations (like dropping columns or tables) are handled safely with explicit down-grades or multi-step migrations.
3. **Linear History:** Maintain a single head revision branch. Never merge divergent migration histories in production.
4. **Execution:** Migrations are executed as part of the deployment pipeline or startup script via:

```bash
alembic upgrade head
```

---

## 3. Indexing Strategies & Performance Tuning

To maintain low-latency query performance as data scales, follow these indexing principles:

- **Foreign Keys:** Every foreign key column must have a corresponding index to optimize JOIN operations and cascading deletes.
- **Frequent Lookups:** Columns frequently used in `WHERE`, `ORDER BY`, or `JOIN` clauses (such as `email`, `status`, or external reference IDs) must be explicitly indexed.
- **Composite Indexes:** When querying multiple columns together frequently, define composite indexes matching the query predicate order.
- **JSONB Indexing:** For columns storing semi-structured metadata as PostgreSQL `JSONB`, apply GIN (Generalized Inverted Index) indexes to support high-performance containment and key-value queries:

```python
Index("ix_module_metadata_gin", TableName.metadata_column, postgresql_using="gin")
```
