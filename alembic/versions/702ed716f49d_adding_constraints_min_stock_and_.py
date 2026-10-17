"""adding constraints, min stock and quantity stock cant be less than zero and any stock movement should be quantity greater than 0

Revision ID: 702ed716f49d
Revises: 1250e130c91b
Create Date: 2026-10-17 11:22:43.633621

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '702ed716f49d'
down_revision: Union[str, Sequence[str], None] = '1250e130c91b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_check_constraint('check_product_stock_quantity_positive', 'products', 'stock_quantity >= 0')
    op.create_check_constraint('check_product_min_stock_positive', 'products', 'minimum_stock >= 0')
    op.create_check_constraint('check_product_cost_price_positive', 'products', 'cost_price >= 0')
    op.create_check_constraint('check_product_sale_price_positive', 'products', 'sale_price >= 0')
    op.create_check_constraint('check_stock_movement_quantity_strictly_positive', 'stock_movements', 'quantity > 0')

    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint('check_product_min_stock_positive', 'products', type_='check')
    op.drop_constraint('check_product_stock_quantity_positive', 'products', type_='check')
    op.drop_constraint('check_product_cost_price_positive', 'products', type_='check')
    op.drop_constraint('check_product_sale_price_positive', 'products', type_='check')
    op.drop_constraint('check_stock_movement_quantity_strictly_positive', 'stock_movements', type_='check')
    # ### end Alembic commands ###
