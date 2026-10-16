from tortoise import migrations
from tortoise.migrations import operations as ops
from models.base import ApprovalAction, ApprovalStatus
from tortoise.fields.base import OnDelete
from tortoise import fields

class Migration(migrations.Migration):
    dependencies = [('models', '0002_auto_20261009_1824')]

    initial = False

    operations = [
        ops.CreateModel(
            name='ApprovalRequest',
            fields=[
                ('id', fields.BigIntField(generated=True, primary_key=True, unique=True, db_index=True)),
                ('created_at', fields.DatetimeField(db_index=True, auto_now=False, auto_now_add=True)),
                ('updated_at', fields.DatetimeField(db_index=True, auto_now=True, auto_now_add=False)),
                ('applicant', fields.ForeignKeyField('models.User', source_field='applicant_id', db_constraint=True, to_field='id', related_name='my_approval_requests', on_delete=OnDelete.CASCADE)),
                ('approver', fields.ForeignKeyField('models.User', source_field='approver_id', null=True, db_constraint=True, to_field='id', related_name='to_approve_requests', on_delete=OnDelete.CASCADE)),
                ('organization', fields.ForeignKeyField('models.Organization', source_field='organization_id', db_constraint=True, to_field='id', related_name='approvals_of_org', on_delete=OnDelete.CASCADE)),
                ('status', fields.CharEnumField(default=ApprovalStatus.DRAFT, description='DRAFT: draft\nPENDING: pending\nAPPROVED: approved\nREJECTED: rejected\nCANCELLED: cancelled', enum_type=ApprovalStatus, max_length=9)),
                ('title', fields.CharField(max_length=200)),
                ('content', fields.TextField(null=True, unique=False)),
            ],
            options={'table': 'approval_request', 'app': 'models', 'pk_attr': 'id'},
            bases=['BaseModel', 'TimestampMixin'],
        ),
        ops.CreateModel(
            name='ApprovalRecord',
            fields=[
                ('id', fields.BigIntField(generated=True, primary_key=True, unique=True, db_index=True)),
                ('created_at', fields.DatetimeField(db_index=True, auto_now=False, auto_now_add=True)),
                ('updated_at', fields.DatetimeField(db_index=True, auto_now=True, auto_now_add=False)),
                ('approval_request', fields.ForeignKeyField('models.ApprovalRequest', source_field='approval_request_id', db_constraint=True, to_field='id', related_name='records', on_delete=OnDelete.CASCADE)),
                ('operator', fields.ForeignKeyField('models.User', source_field='operator_id', db_constraint=True, to_field='id', related_name='approved_record', on_delete=OnDelete.CASCADE)),
                ('action', fields.CharEnumField(description='APPROVE: approve\nREJECT: reject\nCANCEL: cancel\nSUBMIT: submit', enum_type=ApprovalAction, max_length=7)),
                ('comment', fields.TextField(null=True, unique=False)),
                ('operate_at', fields.DatetimeField(auto_now=False, auto_now_add=True)),
            ],
            options={'table': 'approval_record', 'app': 'models', 'pk_attr': 'id'},
            bases=['BaseModel', 'TimestampMixin'],
        ),
    ]
