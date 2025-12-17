"""Create model registry tables

Revision ID: 002_create_model_registry_tables
Revises: 001_create_users_table
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '002_create_model_registry_tables'
down_revision: Union[str, None] = '001_create_users_table'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create modeltype enum
    op.execute("CREATE TYPE modeltype AS ENUM ('sklearn', 'pytorch')")
    
    # Create modelversionsstatus enum
    op.execute("CREATE TYPE modelversionsstatus AS ENUM ('Building', 'Ready', 'Failed')")
    
    # Create models table
    op.create_table(
        'models',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('type', sa.Enum('SKLEARN', 'PYTORCH', name='modeltype'), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_models_id'), 'models', ['id'], unique=False)
    op.create_index(op.f('ix_models_user_id'), 'models', ['user_id'], unique=False)
    
    # Create model_versions table
    op.create_table(
        'model_versions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('model_id', sa.Integer(), nullable=False),
        sa.Column('version_tag', sa.String(), nullable=False),
        sa.Column('s3_path', sa.String(), nullable=False),
        sa.Column('status', sa.Enum('BUILDING', 'READY', 'FAILED', name='modelversionsstatus'), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['model_id'], ['models.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_model_versions_id'), 'model_versions', ['id'], unique=False)
    op.create_index(op.f('ix_model_versions_model_id'), 'model_versions', ['model_id'], unique=False)
    
    # Create deployments table
    op.create_table(
        'deployments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('version_id', sa.Integer(), nullable=False),
        sa.Column('k8s_service_name', sa.String(), nullable=False),
        sa.Column('url', sa.String(), nullable=True),
        sa.Column('replicas', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['version_id'], ['model_versions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('k8s_service_name')
    )
    op.create_index(op.f('ix_deployments_id'), 'deployments', ['id'], unique=False)
    op.create_index(op.f('ix_deployments_version_id'), 'deployments', ['version_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_deployments_version_id'), table_name='deployments')
    op.drop_index(op.f('ix_deployments_id'), table_name='deployments')
    op.drop_table('deployments')
    
    op.drop_index(op.f('ix_model_versions_model_id'), table_name='model_versions')
    op.drop_index(op.f('ix_model_versions_id'), table_name='model_versions')
    op.drop_table('model_versions')
    
    op.drop_index(op.f('ix_models_user_id'), table_name='models')
    op.drop_index(op.f('ix_models_id'), table_name='models')
    op.drop_table('models')
    
    # Drop enums
    sa.Enum(name='modelversionsstatus').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='modeltype').drop(op.get_bind(), checkfirst=True)

