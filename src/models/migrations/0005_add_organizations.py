from tortoise import migrations
from tortoise.migrations import operations as ops
from models.base import OutboxStatus
from tortoise import fields
from tortoise.indexes import Index

class Migration(migrations.Migration):
    dependencies = [('models', '0004_add_organizations')]

    initial = False

    operations = [
        ops.CreateModel(
            name='Notification',
            fields=[
                ('id', fields.BigIntField(generated=True, primary_key=True, unique=True, db_index=True)),
                ('created_at', fields.DatetimeField(db_index=True, auto_now=False, auto_now_add=True)),
                ('updated_at', fields.DatetimeField(db_index=True, auto_now=True, auto_now_add=False)),
                ('user_id', fields.CharField(db_index=True, max_length=64)),
                ('title', fields.CharField(max_length=255)),
                ('content', fields.TextField(unique=False)),
                ('is_read', fields.BooleanField(default=False, db_index=True)),
                ('source_event_id', fields.CharField(unique=True, db_index=True, max_length=64)),
                ('read_at', fields.DatetimeField(null=True, auto_now=False, auto_now_add=False)),
            ],
            options={'table': 'notification', 'app': 'models', 'pk_attr': 'id'},
            bases=['BaseModel', 'TimestampMixin'],
        ),
        ops.CreateModel(
            name='OutboxMessage',
            fields=[
                ('id', fields.BigIntField(generated=True, primary_key=True, unique=True, db_index=True)),
                ('created_at', fields.DatetimeField(db_index=True, auto_now=False, auto_now_add=True)),
                ('updated_at', fields.DatetimeField(db_index=True, auto_now=True, auto_now_add=False)),
                ('event_id', fields.CharField(unique=True, db_index=True, max_length=64)),
                ('event_type', fields.CharField(db_index=True, max_length=128)),
                ('payload', fields.TextField(unique=False)),
                ('status', fields.CharEnumField(default=OutboxStatus.PENDING, db_index=True, description='PENDING: pending\nDELIVERED: delivered\nFAILED: failed', enum_type=OutboxStatus, max_length=9)),
                ('retry_count', fields.IntField(default=0)),
                ('max_retry', fields.IntField(default=3)),
            ],
            options={'table': 'outbox_message', 'app': 'models', 'indexes': [Index(fields=['status', 'created_at'])], 'pk_attr': 'id'},
            bases=['BaseModel', 'TimestampMixin'],
        ),
    ]
