from tortoise import migrations
from tortoise.migrations import operations as ops
import functools
from json import dumps, loads
from models.base import IdeStatus
from tortoise import fields

class Migration(migrations.Migration):
    dependencies = [('models', '0003_auto_20261015_1859')]

    initial = False

    operations = [
        ops.CreateModel(
            name='IdempotencyRecord',
            fields=[
                ('id', fields.BigIntField(generated=True, primary_key=True, unique=True, db_index=True)),
                ('created_at', fields.DatetimeField(db_index=True, auto_now=False, auto_now_add=True)),
                ('updated_at', fields.DatetimeField(db_index=True, auto_now=True, auto_now_add=False)),
                ('idempotency_key', fields.CharField(unique=True, db_index=True, max_length=64)),
                ('request_digest', fields.TextField(unique=False)),
                ('response_data', fields.JSONField(null=True, encoder=functools.partial(dumps, separators=(',', ':')), decoder=loads)),
                ('status', fields.CharEnumField(description='PENDING: pending\nSUCCESS: success\nFAILED: failed', enum_type=IdeStatus, max_length=7)),
            ],
            options={'table': 'idempotency_record', 'app': 'models', 'pk_attr': 'id'},
            bases=['BaseModel', 'TimestampMixin'],
        ),
    ]
