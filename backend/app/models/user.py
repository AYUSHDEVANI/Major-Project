from typing import Optional
from sqlalchemy import String, JSON, Boolean, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from app.models.history import Base
from app.core.security import encrypt_data, decrypt_data


class Company(Base):
    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    created_at: Mapped[str] = mapped_column(String(100), nullable=False)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(50), default="viewer", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.id"), nullable=False)
    
    # Store permissions as JSON array
    permissions: Mapped[list[str]] = mapped_column(JSON, default=list)

    # Encrypted employee metadata
    _encrypted_employee_id: Mapped[Optional[str]] = mapped_column("encrypted_employee_id", String, nullable=True)

    @property
    def employee_id(self) -> Optional[str]:
        if self._encrypted_employee_id:
            return decrypt_data(self._encrypted_employee_id)
        return None

    @employee_id.setter
    def employee_id(self, plain_text_id: Optional[str]):
        if plain_text_id:
            self._encrypted_employee_id = encrypt_data(plain_text_id)
        else:
            self._encrypted_employee_id = None


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    filename: Mapped[str] = mapped_column(String(500), nullable=False)
    source: Mapped[str] = mapped_column(String(500), nullable=False)
    page_count: Mapped[int] = mapped_column(Integer, default=0)
    chunk_count: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    uploaded_by: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    uploaded_at: Mapped[str] = mapped_column(String(100), nullable=False)
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.id"), nullable=False)


class BlacklistedToken(Base):
    __tablename__ = "blacklisted_tokens"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    jti: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
