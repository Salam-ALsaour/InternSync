"""increment 4 schema: evaluation of the company, survey, certificates, retention (Increment 4 design, Section 2)

Revision ID: 0006
Revises: 0005
Create Date: 2026-10-28 10:05:00
"""
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = '0006'
down_revision = '0005'
branch_labels = None
depends_on = None

NEW_TABLES = ("company_evaluations", "outcome_surveys", "certificates")
RATINGS = ("learning_opportunities", "supervision_quality", "work_environment", "relevance_to_major")
# Defaults of Design Table 4.1 for this increment (NFR-MNT-03)
DEFAULTS = {"dashboard.leniency_min_evaluations": 5, "dashboard.leniency_delta": 0.8}


def upgrade() -> None:
    op.create_table('company_evaluations',
    sa.Column('placement_id', sa.UUID(), nullable=False),
    *[sa.Column(r, sa.SmallInteger(), nullable=False) for r in RATINGS],
    sa.Column('would_recommend', sa.Boolean(), nullable=False),
    sa.Column('comment', sa.Text(), nullable=True),
    sa.Column('submitted_at', sa.DateTime(timezone=True), nullable=False),
    *[sa.CheckConstraint(f"{r} BETWEEN 1 AND 5", name=op.f(f'ck_company_evaluations_{r}')) for r in RATINGS],
    sa.ForeignKeyConstraint(['placement_id'], ['placements.id'], name=op.f('fk_company_evaluations_placement_id_placements')),
    sa.PrimaryKeyConstraint('placement_id', name=op.f('pk_company_evaluations'))
    )
    op.create_table('outcome_surveys',
    sa.Column('placement_id', sa.UUID(), nullable=False),
    sa.Column('job_offer', sa.Text(), nullable=False),
    sa.Column('submitted_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint("job_offer IN ('yes','no','pending')", name=op.f('ck_outcome_surveys_job_offer')),
    sa.ForeignKeyConstraint(['placement_id'], ['placements.id'], name=op.f('fk_outcome_surveys_placement_id_placements')),
    sa.PrimaryKeyConstraint('placement_id', name=op.f('pk_outcome_surveys'))
    )
    op.create_table('certificates',
    sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.Column('placement_id', sa.UUID(), nullable=False),
    sa.Column('code', sa.Text(), nullable=False),
    sa.Column('file_id', sa.UUID(), nullable=False),
    sa.Column('status', sa.Text(), server_default=sa.text("'valid'"), nullable=False),
    sa.Column('issued_by', sa.UUID(), nullable=False),
    sa.Column('issued_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('revoked_by', sa.UUID(), nullable=True),
    sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('revoke_reason', sa.Text(), nullable=True),
    sa.CheckConstraint("status IN ('valid','revoked')", name=op.f('ck_certificates_status')),
    sa.CheckConstraint("status <> 'revoked' OR (revoke_reason IS NOT NULL AND length(trim(revoke_reason)) > 0)", name=op.f('ck_certificates_revoke_reason')),
    sa.ForeignKeyConstraint(['file_id'], ['files.id'], name=op.f('fk_certificates_file_id_files')),
    sa.ForeignKeyConstraint(['issued_by'], ['users.id'], name=op.f('fk_certificates_issued_by_users')),
    sa.ForeignKeyConstraint(['placement_id'], ['placements.id'], name=op.f('fk_certificates_placement_id_placements')),
    sa.ForeignKeyConstraint(['revoked_by'], ['users.id'], name=op.f('fk_certificates_revoked_by_users')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_certificates')),
    sa.UniqueConstraint('code', name=op.f('uq_certificates_code'))
    )
    op.create_index('uq_certificates_valid_placement', 'certificates', ['placement_id'], unique=True, postgresql_where=sa.text("status = 'valid'"))
    op.add_column('colleges', sa.Column('retention_months', sa.SmallInteger(), server_default=sa.text('12'), nullable=False))
    op.create_check_constraint(op.f('ck_colleges_retention_months'), 'colleges', 'retention_months BETWEEN 0 AND 120')
    op.add_column('training_cycles', sa.Column('anonymized_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('training_cycles', sa.Column('anonymized_by', sa.UUID(), nullable=True))
    op.create_foreign_key(op.f('fk_training_cycles_anonymized_by_users'), 'training_cycles', 'users', ['anonymized_by'], ['id'])
    op.add_column('users', sa.Column('anonymized_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('files', sa.Column('purged_at', sa.DateTime(timezone=True), nullable=True))
    for table in NEW_TABLES:  # as migration 0003 did for the earlier tables
        op.execute(f"ALTER TABLE public.{table} ENABLE ROW LEVEL SECURITY")
    settings = sa.table("system_settings", sa.column("key", sa.Text), sa.column("value", postgresql.JSONB))
    op.bulk_insert(settings, [{"key": k, "value": v} for k, v in DEFAULTS.items()])


def downgrade() -> None:
    op.execute("DELETE FROM system_settings WHERE key LIKE 'dashboard.leniency_%'")
    op.drop_column('files', 'purged_at')
    op.drop_column('users', 'anonymized_at')
    op.drop_constraint(op.f('fk_training_cycles_anonymized_by_users'), 'training_cycles', type_='foreignkey')
    op.drop_column('training_cycles', 'anonymized_by')
    op.drop_column('training_cycles', 'anonymized_at')
    op.drop_constraint(op.f('ck_colleges_retention_months'), 'colleges', type_='check')
    op.drop_column('colleges', 'retention_months')
    op.drop_index('uq_certificates_valid_placement', table_name='certificates', postgresql_where=sa.text("status = 'valid'"))
    op.drop_table('certificates')
    op.drop_table('outcome_surveys')
    op.drop_table('company_evaluations')
