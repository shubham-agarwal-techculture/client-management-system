"""Initial schema

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-06-02 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "organizations",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("slug", sa.String(length=100), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_organizations_slug"), "organizations", ["slug"], unique=True)
    op.create_index(op.f("ix_organizations_name"), "organizations", ["name"], unique=False)

    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=200), nullable=True),
        sa.Column("role", sa.String(length=50), nullable=False, server_default=sa.text("'agent'")),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("organization_id", sa.Uuid(), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)
    op.create_index(op.f("ix_users_role"), "users", ["role"], unique=False)
    op.create_index(op.f("ix_users_organization_id"), "users", ["organization_id"], unique=False)

    op.create_table(
        "clients",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=True),
        sa.Column("owner_id", sa.Uuid(), nullable=True),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("client_type", sa.String(length=100), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False, server_default=sa.text("'active'")),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("phone", sa.String(length=50), nullable=True),
        sa.Column("website", sa.String(length=200), nullable=True),
        sa.Column("address", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("is_archived", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_clients_name"), "clients", ["name"], unique=False)
    op.create_index(op.f("ix_clients_client_type"), "clients", ["client_type"], unique=False)
    op.create_index(op.f("ix_clients_status"), "clients", ["status"], unique=False)
    op.create_index(op.f("ix_clients_organization_id"), "clients", ["organization_id"], unique=False)
    op.create_index(op.f("ix_clients_owner_id"), "clients", ["owner_id"], unique=False)

    op.create_table(
        "custom_fields",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=True),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("field_type", sa.String(length=30), nullable=False),
        sa.Column("options", sa.Text(), nullable=True),
        sa.Column("required", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_custom_fields_name"), "custom_fields", ["name"], unique=False)
    op.create_index(op.f("ix_custom_fields_organization_id"), "custom_fields", ["organization_id"], unique=False)

    op.create_table(
        "client_custom_values",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("client_id", sa.Uuid(), nullable=False),
        sa.Column("field_id", sa.Uuid(), nullable=False),
        sa.Column("value", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["client_id"], ["clients.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["field_id"], ["custom_fields.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("client_id", "field_id", name="uq_client_custom_values_client_field"),
    )
    op.create_index(op.f("ix_client_custom_values_client_id"), "client_custom_values", ["client_id"], unique=False)
    op.create_index(op.f("ix_client_custom_values_field_id"), "client_custom_values", ["field_id"], unique=False)

    op.create_table(
        "tags",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=True),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("color", sa.String(length=20), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_tags_name"), "tags", ["name"], unique=False)
    op.create_index(op.f("ix_tags_organization_id"), "tags", ["organization_id"], unique=False)

    op.create_table(
        "client_tags",
        sa.Column("client_id", sa.Uuid(), nullable=False),
        sa.Column("tag_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["client_id"], ["clients.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tag_id"], ["tags.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("client_id", "tag_id"),
    )

    op.create_table(
        "interactions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=True),
        sa.Column("client_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=True),
        sa.Column("interaction_type", sa.String(length=50), nullable=False),
        sa.Column("direction", sa.String(length=20), nullable=True),
        sa.Column("subject", sa.String(length=200), nullable=True),
        sa.Column("body", sa.Text(), nullable=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["client_id"], ["clients.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_interactions_client_id"), "interactions", ["client_id"], unique=False)
    op.create_index(op.f("ix_interactions_interaction_type"), "interactions", ["interaction_type"], unique=False)
    op.create_index(op.f("ix_interactions_occurred_at"), "interactions", ["occurred_at"], unique=False)
    op.create_index(op.f("ix_interactions_organization_id"), "interactions", ["organization_id"], unique=False)

    op.create_table(
        "tasks",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=True),
        sa.Column("client_id", sa.Uuid(), nullable=True),
        sa.Column("assignee_id", sa.Uuid(), nullable=True),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False, server_default=sa.text("'todo'")),
        sa.Column("priority", sa.String(length=20), nullable=False, server_default=sa.text("'medium'")),
        sa.Column("due_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["client_id"], ["clients.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["assignee_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_tasks_client_id"), "tasks", ["client_id"], unique=False)
    op.create_index(op.f("ix_tasks_status"), "tasks", ["status"], unique=False)
    op.create_index(op.f("ix_tasks_priority"), "tasks", ["priority"], unique=False)
    op.create_index(op.f("ix_tasks_due_date"), "tasks", ["due_date"], unique=False)
    op.create_index(op.f("ix_tasks_assignee_id"), "tasks", ["assignee_id"], unique=False)
    op.create_index(op.f("ix_tasks_organization_id"), "tasks", ["organization_id"], unique=False)

    op.create_table(
        "documents",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=True),
        sa.Column("client_id", sa.Uuid(), nullable=True),
        sa.Column("uploaded_by_id", sa.Uuid(), nullable=True),
        sa.Column("filename", sa.String(length=300), nullable=False),
        sa.Column("storage_path", sa.String(length=500), nullable=False),
        sa.Column("mime_type", sa.String(length=100), nullable=True),
        sa.Column("size_bytes", sa.BigInteger(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["client_id"], ["clients.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["uploaded_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_documents_client_id"), "documents", ["client_id"], unique=False)
    op.create_index(op.f("ix_documents_organization_id"), "documents", ["organization_id"], unique=False)

    op.create_table(
        "event_logs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=True),
        sa.Column("actor_user_id", sa.Uuid(), nullable=True),
        sa.Column("action", sa.String(length=100), nullable=False),
        sa.Column("entity_type", sa.String(length=100), nullable=False),
        sa.Column("entity_id", sa.String(length=255), nullable=True),
        sa.Column("metadata", sa.Text(), nullable=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_event_logs_action"), "event_logs", ["action"], unique=False)
    op.create_index(op.f("ix_event_logs_entity_type"), "event_logs", ["entity_type"], unique=False)
    op.create_index(op.f("ix_event_logs_entity_id"), "event_logs", ["entity_id"], unique=False)
    op.create_index(op.f("ix_event_logs_organization_id"), "event_logs", ["organization_id"], unique=False)
    op.create_index(op.f("ix_event_logs_occurred_at"), "event_logs", ["occurred_at"], unique=False)


def downgrade() -> None:
    op.drop_table("event_logs")
    op.drop_table("documents")
    op.drop_table("tasks")
    op.drop_table("interactions")
    op.drop_table("client_tags")
    op.drop_table("tags")
    op.drop_table("client_custom_values")
    op.drop_table("custom_fields")
    op.drop_table("clients")
    op.drop_table("users")
    op.drop_table("organizations")