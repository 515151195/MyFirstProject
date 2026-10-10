from tortoise import migrations
from tortoise.migrations import operations as ops
from models.base import InvitationStatus, MembershipStatus, OrgMemberRole, OrgStatus
from tortoise.fields.base import OnDelete
from tortoise import fields

class Migration(migrations.Migration):
    dependencies = [('models', '0001_initial')]

    initial = False

    operations = [
        ops.CreateModel(
            name='Organization',
            fields=[
                ('id', fields.BigIntField(generated=True, primary_key=True, unique=True, db_index=True)),
                ('created_at', fields.DatetimeField(db_index=True, auto_now=False, auto_now_add=True)),
                ('updated_at', fields.DatetimeField(db_index=True, auto_now=True, auto_now_add=False)),
                ('name', fields.CharField(unique=True, db_index=True, max_length=32)),
                ('desc', fields.CharField(max_length=255)),
                ('status', fields.CharEnumField(default=OrgStatus.PENDING, description='ACTIVE: active\nDISABLED: disabled\nPENDING: pending', enum_type=OrgStatus, max_length=8)),
                ('owner', fields.ForeignKeyField('models.User', source_field='owner_id', db_constraint=True, to_field='id', related_name='owned_orgs', on_delete=OnDelete.CASCADE)),
            ],
            options={'table': 'Organization', 'app': 'models', 'pk_attr': 'id'},
            bases=['BaseModel', 'TimestampMixin'],
        ),
        ops.CreateModel(
            name='Invitation',
            fields=[
                ('id', fields.BigIntField(generated=True, primary_key=True, unique=True, db_index=True)),
                ('created_at', fields.DatetimeField(db_index=True, auto_now=False, auto_now_add=True)),
                ('updated_at', fields.DatetimeField(db_index=True, auto_now=True, auto_now_add=False)),
                ('org', fields.ForeignKeyField('models.Organization', source_field='org_id', db_constraint=True, to_field='id', related_name='invitations', on_delete=OnDelete.CASCADE)),
                ('inviter', fields.ForeignKeyField('models.User', source_field='inviter_id', db_constraint=True, to_field='id', related_name='sent_invitations', on_delete=OnDelete.CASCADE)),
                ('invitee_email', fields.CharField(max_length=128)),
                ('role', fields.CharEnumField(description='OWNER: owner\nADMIN: admin\nMEMBER: member\nVIEWER: viewer', enum_type=OrgMemberRole, max_length=6)),
                ('token_hash', fields.CharField(max_length=255)),
                ('expire_at', fields.DatetimeField(auto_now=False, auto_now_add=False)),
                ('status', fields.CharEnumField(default=InvitationStatus.PENDING, description='PENDING: pending\nUSED: used\nEXPIRED: expired\nREVOKED: revoked', enum_type=InvitationStatus, max_length=7)),
            ],
            options={'table': 'invitations', 'app': 'models', 'pk_attr': 'id'},
            bases=['BaseModel', 'TimestampMixin'],
        ),
        ops.CreateModel(
            name='Membership',
            fields=[
                ('id', fields.BigIntField(generated=True, primary_key=True, unique=True, db_index=True)),
                ('created_at', fields.DatetimeField(db_index=True, auto_now=False, auto_now_add=True)),
                ('updated_at', fields.DatetimeField(db_index=True, auto_now=True, auto_now_add=False)),
                ('user', fields.ForeignKeyField('models.User', source_field='user_id', db_constraint=True, to_field='id', related_name='memberships', on_delete=OnDelete.CASCADE)),
                ('org', fields.ForeignKeyField('models.Organization', source_field='org_id', db_constraint=True, to_field='id', related_name='members', on_delete=OnDelete.CASCADE)),
                ('role', fields.CharEnumField(description='OWNER: owner\nADMIN: admin\nMEMBER: member\nVIEWER: viewer', enum_type=OrgMemberRole, max_length=6)),
                ('status', fields.CharEnumField(default=MembershipStatus.ACTIVE, description='ACTIVE: active\nDISABLED: disabled', enum_type=MembershipStatus, max_length=8)),
            ],
            options={'table': 'Membership', 'app': 'models', 'unique_together': (('user', 'org'),), 'pk_attr': 'id'},
            bases=['BaseModel', 'TimestampMixin'],
        ),
    ]
