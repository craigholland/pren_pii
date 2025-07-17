from pii.database.models.core.main import db
from pii.database.models.core.service_object import ServiceObject
from sqlalchemy import Column, Integer, String, Boolean, UUID
from sqlalchemy.orm import mapped_column

# class User(ServiceObject, db.Model):
#     __tablename__ = "users"
#
#     username = mapped_column(String(255), unique=True, nullable=False)
#     password = mapped_column(String(255), nullable=False)
#     email = mapped_column(String(255), unique=True, nullable=False)
#     is_active = mapped_column(Boolean, default=True)
#     is_admin = mapped_column(Boolean, default=False)