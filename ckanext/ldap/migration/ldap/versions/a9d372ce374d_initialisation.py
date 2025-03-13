"""
Initialisation.

Revision ID: a9d372ce374d
Revises:
Create Date: 2025-03-12 15:53:47.144577
"""

from datetime import datetime as dt

import sqlalchemy as sa
from alembic import op
from ckan import model
from sqlalchemy.engine.reflection import Inspector

# revision identifiers, used by Alembic.
revision = 'a9d372ce374d'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # check if the table already exists
    bind = op.get_bind()
    insp = Inspector.from_engine(bind)
    all_table_names = insp.get_table_names()
    table_exists = 'ldap_user' in all_table_names

    if not table_exists:
        op.create_table(
            'ldap_user',
            sa.Column(
                'id', sa.UnicodeText, primary_key=True, default=model.types.make_uuid
            ),
            sa.Column(
                'user_id',
                sa.UnicodeText,
                sa.ForeignKey('user.id'),
                unique=True,
                nullable=False,
            ),
            sa.Column(
                'ldap_id', sa.UnicodeText, index=True, unique=True, nullable=False
            ),
            sa.Column('created', sa.DateTime, default=dt.now),
        )


def downgrade():
    op.drop_table('ldap_user')
