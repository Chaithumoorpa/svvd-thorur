"""Convert members to standalone temple_members

Revision ID: c8f9a2b3d4e5
Revises: b385f6d4d9e5
Create Date: 2026-01-01 07:58:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'c8f9a2b3d4e5'
down_revision = 'b385f6d4d9e5'
branch_labels = None
depends_on = None


def upgrade():
    # Get connection and inspector
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = inspector.get_table_names()
    
    # Determine which table exists
    if 'members' in tables:
        source_table = 'members'
    elif 'temple_members' in tables:
        source_table = 'temple_members'
    else:
        # No table exists, nothing to migrate
        return
    
    # Get current columns
    columns = [c['name'] for c in inspector.get_columns(source_table)]
    
    # Drop foreign key constraint if it exists
    try:
        constraints = [c['name'] for c in inspector.get_foreign_keys(source_table)]
        for constraint_name in constraints:
            if 'user_id' in constraint_name:
                op.drop_constraint(constraint_name, source_table, type_='foreignkey')
    except:
        pass  # Constraint might not exist
    
    # Drop old columns if they exist
    for col in ['user_id', 'full_name', 'designation', 'department', 'joining_date', 'address', 'emergency_contact']:
        if col in columns:
            op.drop_column(source_table, col)
    
    # Refresh column list
    columns = [c['name'] for c in inspector.get_columns(source_table)]
    
    # Add new columns if they don't exist
    if 'name' not in columns:
        op.add_column(source_table, sa.Column('name', sa.String(length=200), nullable=False, server_default=''))
        op.alter_column(source_table, 'name', server_default=None)
    
    if 'phone' not in columns:
        op.add_column(source_table, sa.Column('phone', sa.String(length=50), nullable=False, server_default=''))
        op.alter_column(source_table, 'phone', server_default=None)
    
    if 'email' not in columns:
        op.add_column(source_table, sa.Column('email', sa.String(length=200), nullable=True))
    
    if 'role' not in columns:
        op.add_column(source_table, sa.Column('role', sa.String(length=100), nullable=True))
    
    # Rename table if needed
    if source_table == 'members':
        op.rename_table('members', 'temple_members')


def downgrade():
    # Remove new columns
    op.drop_column('temple_members', 'role')
    op.drop_column('temple_members', 'email')
    op.drop_column('temple_members', 'phone')
    op.drop_column('temple_members', 'name')
    
    # Add back old columns
    op.add_column('temple_members', sa.Column('user_id', sa.INTEGER(), nullable=False))
    op.add_column('temple_members', sa.Column('full_name', sa.VARCHAR(length=200), nullable=False))
    op.add_column('temple_members', sa.Column('designation', sa.VARCHAR(length=100), nullable=True))
    op.add_column('temple_members', sa.Column('department', sa.VARCHAR(length=100), nullable=True))
    op.add_column('temple_members', sa.Column('joining_date', postgresql.TIMESTAMP(), nullable=True))
    op.add_column('temple_members', sa.Column('address', sa.VARCHAR(length=500), nullable=True))
    op.add_column('temple_members', sa.Column('emergency_contact', sa.VARCHAR(length=50), nullable=True))
    
    # Recreate foreign key constraint
    op.create_foreign_key('temple_members_user_id_fkey', 'temple_members', 'users', ['user_id'], ['id'], ondelete='CASCADE')
    
    # Rename table back
    op.rename_table('temple_members', 'members')
