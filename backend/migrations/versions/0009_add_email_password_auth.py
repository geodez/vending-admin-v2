"""add email and password authentication

Revision ID: 0009
Revises: 0008_update_views_remove_machine_matrix
Create Date: 2026-02-13 22:50:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0009_add_email_password_auth'
down_revision = '0008_update_views_remove_machine_matrix'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Добавляем новые колонки для email/password авторизации
    # 1. Делаем telegram_user_id nullable (для пользователей без Telegram)
    op.alter_column('users', 'telegram_user_id',
                    existing_type=sa.BigInteger(),
                    nullable=True)
    
    # 2. Добавляем email колонку
    op.add_column('users', sa.Column('email', sa.String(), nullable=True))
    
    # 3. Добавляем hashed_password колонку
    op.add_column('users', sa.Column('hashed_password', sa.String(), nullable=True))
    
    # 4. Создаем индекс для email
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)


def downgrade() -> None:
    # Удаляем индекс email
    op.drop_index(op.f('ix_users_email'), table_name='users')
    
    # Удаляем колонки
    op.drop_column('users', 'hashed_password')
    op.drop_column('users', 'email')
    
    # Возвращаем telegram_user_id обратно в NOT NULL
    op.alter_column('users', 'telegram_user_id',
                    existing_type=sa.BigInteger(),
                    nullable=False)
