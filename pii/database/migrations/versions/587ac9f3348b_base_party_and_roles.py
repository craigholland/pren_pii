"""base party and roles

Revision ID: 587ac9f3348b
Revises: dbdd6dc871fe
Create Date: 2025-07-18 10:10:18.276446

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '587ac9f3348b'
down_revision = '6345b65750fc'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('party',
    sa.Column('type', sa.String(length=50), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('notes', sa.String(), nullable=True),
    sa.Column('id', sa.UUID(), server_default=sa.text('uuid_generate_v4()'), nullable=False),
    sa.Column('date_created', sa.DateTime(timezone=True), server_default=sa.text('clock_timestamp()'), nullable=True),
    sa.Column('last_updated', sa.DateTime(timezone=True), server_default=sa.text('clock_timestamp()'), nullable=True),
    sa.Column('data_origin', sa.Text(), nullable=True),
    sa.Column('_metadata', sa.JSON(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('organization',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('legal_name', sa.String(length=255), nullable=False),
    sa.Column('registration_number', sa.String(length=100), nullable=True),
    sa.Column('org_type', sa.String(length=100), nullable=True),
    sa.ForeignKeyConstraint(['id'], ['party.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('party_role',
    sa.Column('type', sa.String(length=100), nullable=False),
    sa.Column('party_id', sa.UUID(), nullable=False),
    sa.Column('terminated', sa.Boolean(), nullable=False),
    sa.Column('id', sa.UUID(), server_default=sa.text('uuid_generate_v4()'), nullable=False),
    sa.Column('date_created', sa.DateTime(timezone=True), server_default=sa.text('clock_timestamp()'), nullable=True),
    sa.Column('last_updated', sa.DateTime(timezone=True), server_default=sa.text('clock_timestamp()'), nullable=True),
    sa.Column('data_origin', sa.Text(), nullable=True),
    sa.Column('_metadata', sa.JSON(), nullable=True),
    sa.ForeignKeyConstraint(['party_id'], ['party.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_party_role_party_id'), 'party_role', ['party_id'], unique=False)
    op.create_index(op.f('ix_party_role_terminated'), 'party_role', ['terminated'], unique=False)
    op.create_index(op.f('ix_party_role_type'), 'party_role', ['type'], unique=False)
    op.create_table('person',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('date_of_birth', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['id'], ['party.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('marital_status',
    sa.Column('status', sa.Enum('SINGLE', 'MARRIED', 'DIVORCED', 'WIDOWED', 'SEPARATED', 'PARTNERED', 'UNKNOWN', name='maritalstatustype'), nullable=False),
    sa.Column('person_id', sa.UUID(), nullable=False),
    sa.Column('start_date', sa.DateTime(), nullable=False),
    sa.Column('end_date', sa.DateTime(), nullable=True),
    sa.Column('id', sa.UUID(), server_default=sa.text('uuid_generate_v4()'), nullable=False),
    sa.Column('date_created', sa.DateTime(timezone=True), server_default=sa.text('clock_timestamp()'), nullable=True),
    sa.Column('last_updated', sa.DateTime(timezone=True), server_default=sa.text('clock_timestamp()'), nullable=True),
    sa.Column('data_origin', sa.Text(), nullable=True),
    sa.Column('_metadata', sa.JSON(), nullable=True),
    sa.ForeignKeyConstraint(['person_id'], ['person.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('organization_managed_person_association',
    sa.Column('organization_role_id', sa.UUID(), nullable=False),
    sa.Column('person_role_id', sa.UUID(), nullable=False),
    sa.Column('id', sa.UUID(), server_default=sa.text('uuid_generate_v4()'), nullable=False),
    sa.Column('date_created', sa.DateTime(timezone=True), server_default=sa.text('clock_timestamp()'), nullable=True),
    sa.Column('last_updated', sa.DateTime(timezone=True), server_default=sa.text('clock_timestamp()'), nullable=True),
    sa.Column('data_origin', sa.Text(), nullable=True),
    sa.Column('_metadata', sa.JSON(), nullable=True),
    sa.ForeignKeyConstraint(['organization_role_id'], ['party_role.id'], ),
    sa.ForeignKeyConstraint(['person_role_id'], ['party_role.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('organization_role_id', 'person_role_id', name='uix_managed_person_organization')
    )
    op.create_index(op.f('ix_organization_managed_person_association_organization_role_id'), 'organization_managed_person_association', ['organization_role_id'], unique=False)
    op.create_index(op.f('ix_organization_managed_person_association_person_role_id'), 'organization_managed_person_association', ['person_role_id'], unique=False)
    op.create_table('organization_owner_association',
    sa.Column('organization_role_id', sa.UUID(), nullable=False),
    sa.Column('person_role_id', sa.UUID(), nullable=False),
    sa.Column('id', sa.UUID(), server_default=sa.text('uuid_generate_v4()'), nullable=False),
    sa.Column('date_created', sa.DateTime(timezone=True), server_default=sa.text('clock_timestamp()'), nullable=True),
    sa.Column('last_updated', sa.DateTime(timezone=True), server_default=sa.text('clock_timestamp()'), nullable=True),
    sa.Column('data_origin', sa.Text(), nullable=True),
    sa.Column('_metadata', sa.JSON(), nullable=True),
    sa.ForeignKeyConstraint(['organization_role_id'], ['party_role.id'], ),
    sa.ForeignKeyConstraint(['person_role_id'], ['party_role.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('organization_role_id', 'person_role_id', name='uix_owner_organization')
    )
    op.create_index(op.f('ix_organization_owner_association_organization_role_id'), 'organization_owner_association', ['organization_role_id'], unique=False)
    op.create_index(op.f('ix_organization_owner_association_person_role_id'), 'organization_owner_association', ['person_role_id'], unique=False)
    op.create_table('organization_staff_assoc',
    sa.Column('organization_id', sa.UUID(), nullable=False),
    sa.Column('staff_person_id', sa.UUID(), nullable=False),
    sa.Column('id', sa.UUID(), server_default=sa.text('uuid_generate_v4()'), nullable=False),
    sa.Column('date_created', sa.DateTime(timezone=True), server_default=sa.text('clock_timestamp()'), nullable=True),
    sa.Column('last_updated', sa.DateTime(timezone=True), server_default=sa.text('clock_timestamp()'), nullable=True),
    sa.Column('data_origin', sa.Text(), nullable=True),
    sa.Column('_metadata', sa.JSON(), nullable=True),
    sa.ForeignKeyConstraint(['organization_id'], ['organization.id'], ),
    sa.ForeignKeyConstraint(['staff_person_id'], ['person.id'], ),
    sa.PrimaryKeyConstraint('organization_id', 'staff_person_id', 'id'),
    sa.UniqueConstraint('organization_id', 'staff_person_id', name='uq_org_staff')
    )
    op.create_table('organization_to_parent_org',
    sa.Column('child_org_id', sa.UUID(), nullable=False),
    sa.Column('parent_org_id', sa.UUID(), nullable=False),
    sa.Column('id', sa.UUID(), server_default=sa.text('uuid_generate_v4()'), nullable=False),
    sa.Column('date_created', sa.DateTime(timezone=True), server_default=sa.text('clock_timestamp()'), nullable=True),
    sa.Column('last_updated', sa.DateTime(timezone=True), server_default=sa.text('clock_timestamp()'), nullable=True),
    sa.Column('data_origin', sa.Text(), nullable=True),
    sa.Column('_metadata', sa.JSON(), nullable=True),
    sa.ForeignKeyConstraint(['child_org_id'], ['organization.id'], ),
    sa.ForeignKeyConstraint(['parent_org_id'], ['organization.id'], ),
    sa.PrimaryKeyConstraint('child_org_id', 'parent_org_id', 'id')
    )
    op.create_table('person_gender',
    sa.Column('gender', sa.Enum('MALE', 'TRANS_MALE', 'FEMALE', 'TRANS_FEMALE', 'NON_BINARY', 'OTHER', 'UNDISCLOSED', name='gendertype'), nullable=False),
    sa.Column('person_id', sa.UUID(), nullable=False),
    sa.Column('start_date', sa.DateTime(), nullable=False),
    sa.Column('end_date', sa.DateTime(), nullable=True),
    sa.Column('id', sa.UUID(), server_default=sa.text('uuid_generate_v4()'), nullable=False),
    sa.Column('date_created', sa.DateTime(timezone=True), server_default=sa.text('clock_timestamp()'), nullable=True),
    sa.Column('last_updated', sa.DateTime(timezone=True), server_default=sa.text('clock_timestamp()'), nullable=True),
    sa.Column('data_origin', sa.Text(), nullable=True),
    sa.Column('_metadata', sa.JSON(), nullable=True),
    sa.ForeignKeyConstraint(['person_id'], ['person.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('person_name',
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('name_type', sa.Enum('FIRST', 'LAST', 'MIDDLE', 'ALIAS', 'NICKNAME', 'PREFIX', 'SUFFIX', 'INITIALS', 'PREFERRED', name='personnametype'), nullable=False),
    sa.Column('person_id', sa.UUID(), nullable=False),
    sa.Column('start_date', sa.DateTime(), nullable=False),
    sa.Column('end_date', sa.DateTime(), nullable=True),
    sa.Column('id', sa.UUID(), server_default=sa.text('uuid_generate_v4()'), nullable=False),
    sa.Column('date_created', sa.DateTime(timezone=True), server_default=sa.text('clock_timestamp()'), nullable=True),
    sa.Column('last_updated', sa.DateTime(timezone=True), server_default=sa.text('clock_timestamp()'), nullable=True),
    sa.Column('data_origin', sa.Text(), nullable=True),
    sa.Column('_metadata', sa.JSON(), nullable=True),
    sa.ForeignKeyConstraint(['person_id'], ['person.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('person_name')
    op.drop_table('person_gender')
    op.drop_table('organization_to_parent_org')
    op.drop_table('organization_staff_assoc')
    op.drop_index(op.f('ix_organization_owner_association_person_role_id'), table_name='organization_owner_association')
    op.drop_index(op.f('ix_organization_owner_association_organization_role_id'), table_name='organization_owner_association')
    op.drop_table('organization_owner_association')
    op.drop_index(op.f('ix_organization_managed_person_association_person_role_id'), table_name='organization_managed_person_association')
    op.drop_index(op.f('ix_organization_managed_person_association_organization_role_id'), table_name='organization_managed_person_association')
    op.drop_table('organization_managed_person_association')
    op.drop_table('marital_status')
    op.drop_table('person')
    op.drop_index(op.f('ix_party_role_type'), table_name='party_role')
    op.drop_index(op.f('ix_party_role_terminated'), table_name='party_role')
    op.drop_index(op.f('ix_party_role_party_id'), table_name='party_role')
    op.drop_table('party_role')
    op.drop_table('organization')
    op.drop_table('party')
    op.execute('DROP TYPE IF EXISTS gendertype;')
    op.execute('DROP TYPE IF EXISTS maritalstatustype;')
    op.execute('DROP TYPE IF EXISTS personnametype;')
    # ### end Alembic commands ###
