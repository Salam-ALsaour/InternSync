"""skill synonyms added in Increment 2 for existing databases (Increment 2 design, Section 12)

The seed adds missing skills but never changes existing ones, so that the Platform Admin's edits stay. The synonyms
that raised Arabic skill extraction in Increment 2 reach databases created earlier through this one-time step; a
synonym the skill already has is left alone. `term` is the synonym's normal form (`app.ai.text.normalize`).

Revision ID: 0004
Revises: 0003
Create Date: 2026-10-26 02:40:00
"""
import sqlalchemy as sa

from alembic import op

revision = '0004'
down_revision = '0003'
branch_labels = None
depends_on = None

ADDED = [  # (skill, synonym, normal form)
    ("Data Visualization", "لوحات مؤشرات", "لوحات مؤشرات"),
    ("Cybersecurity", "أمن سيبراني", "امن سيبراني"),
    ("Networking", "networks", "networks"),
    ("Unit Testing", "اختبارات الوحدات", "اختبارات الوحدات"),
    ("UX Design", "تجربة المستخدم", "تجربه المستخدم"),
    ("Responsive Design", "تصميم متجاوب", "تصميم متجاوب"),
]


def upgrade() -> None:
    add = sa.text("""
        UPDATE skills SET synonyms = array_append(synonyms, :syn),
               match_terms = ARRAY(SELECT DISTINCT t FROM unnest(array_append(match_terms, :term)) AS t ORDER BY t),
               updated_at = now()
        WHERE lower(name_en) = lower(:skill) AND NOT (:syn = ANY(synonyms))""")
    for skill, syn, term in ADDED:
        op.execute(add.bindparams(skill=skill, syn=syn, term=term))


def downgrade() -> None:
    remove = sa.text("""
        UPDATE skills SET synonyms = array_remove(synonyms, :syn), match_terms = array_remove(match_terms, :term)
        WHERE lower(name_en) = lower(:skill) AND :syn = ANY(synonyms)""")
    for skill, syn, term in ADDED:
        op.execute(remove.bindparams(skill=skill, syn=syn, term=term))
