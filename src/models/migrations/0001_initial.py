from tortoise import migrations
from tortoise.migrations import operations as ops
from tortoise.fields.base import OnDelete
from tortoise import fields

class Migration(migrations.Migration):
    initial = True

    operations = [
        ops.CreateModel(
            name='Role',
            fields=[
                ('id', fields.BigIntField(generated=True, primary_key=True, unique=True, db_index=True)),
                ('created_at', fields.DatetimeField(db_index=True, auto_now=False, auto_now_add=True)),
                ('updated_at', fields.DatetimeField(db_index=True, auto_now=True, auto_now_add=False)),
                ('name', fields.CharField(unique=True, db_index=True, max_length=20)),
                ('desc', fields.CharField(max_length=255)),
            ],
            options={'table': 'role', 'app': 'models', 'pk_attr': 'id'},
            bases=['BaseModel', 'TimestampMixin'],
        ),
        ops.CreateModel(
            name='User',
            fields=[
                ('id', fields.BigIntField(generated=True, primary_key=True, unique=True, db_index=True)),
                ('created_at', fields.DatetimeField(db_index=True, auto_now=False, auto_now_add=True)),
                ('updated_at', fields.DatetimeField(db_index=True, auto_now=True, auto_now_add=False)),
                ('username', fields.CharField(unique=True, db_index=True, max_length=20)),
                ('email', fields.CharField(unique=True, db_index=True, max_length=255)),
                ('password', fields.CharField(max_length=128)),
                ('is_active', fields.BooleanField(default=True)),
                ('is_superuser', fields.BooleanField(default=False)),
                ('last_login', fields.DatetimeField(null=True, auto_now=False, auto_now_add=False)),
                ('roles', fields.ManyToManyField('models.Role', unique=True, db_constraint=True, through='user_role', forward_key='role_id', backward_key='user_id', related_name='users', on_delete=OnDelete.CASCADE)),
            ],
            options={'table': 'user', 'app': 'models', 'pk_attr': 'id'},
            bases=['BaseModel', 'TimestampMixin'],
        ),
    ]
