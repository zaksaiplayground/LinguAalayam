"""Update word_column as non-nullable to word_definition

Revision ID: d0e4ebf54ede
Revises: d9da4a7bb619
Create Date: 2025-05-10 23:31:05.864636

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd0e4ebf54ede'
down_revision: Union[str, None] = 'd9da4a7bb619'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('word_definition', 'word',
               existing_type=sa.TEXT(),
               nullable=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('word_definition', 'word',
               existing_type=sa.TEXT(),
               nullable=True)
    # ### end Alembic commands ###
