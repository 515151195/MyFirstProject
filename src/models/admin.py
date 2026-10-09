from tortoise import fields

from .base import TimestampMixin, BaseModel

class User(BaseModel, TimestampMixin):
    username = fields.CharField(max_length=20, min_length=2, unique=True, index=True)
    email = fields.CharField(max_length=255, unique=True, index=True)
    password = fields.CharField(max_length=128)
    is_active = fields.BooleanField(default=True)
    is_superuser = fields.BooleanField(default=False)
    last_login = fields.DatetimeField(null=True)
    roles = fields.ManyToManyField("models.Role", related_name="users")

    class Meta:
        table = "user"


class Role(BaseModel, TimestampMixin):
    name = fields.CharField(max_length=20, unique=True, index=True)
    desc = fields.CharField(max_length=255)

    class Meta:
        table = "role"