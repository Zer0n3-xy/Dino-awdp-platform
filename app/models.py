import datetime as dt

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(32), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=dt.datetime.utcnow)

    memberships = relationship("TeamMember", back_populates="user")


class Team(Base):
    __tablename__ = "teams"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    invite_code: Mapped[str] = mapped_column(String(16), unique=True, nullable=False, index=True)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=dt.datetime.utcnow)

    members = relationship("TeamMember", back_populates="team")


class TeamMember(Base):
    __tablename__ = "team_members"
    __table_args__ = (UniqueConstraint("user_id", "team_id", name="uq_user_team"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), nullable=False)
    is_captain: Mapped[bool] = mapped_column(Boolean, default=False)

    user = relationship("User", back_populates="memberships")
    team = relationship("Team", back_populates="members")


class Challenge(Base):
    __tablename__ = "challenges"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    flag: Mapped[str] = mapped_column(String(128), nullable=False)
    score_flag: Mapped[int] = mapped_column(Integer, default=100)
    score_patch: Mapped[int] = mapped_column(Integer, default=150)
    vulnerability_signature: Mapped[str] = mapped_column(String(128), default="FIXED")


class DynamicContainer(Base):
    __tablename__ = "dynamic_containers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), nullable=False)
    challenge_id: Mapped[int] = mapped_column(ForeignKey("challenges.id"), nullable=False)
    endpoint: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(16), default="running")
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=dt.datetime.utcnow)


class FlagSubmission(Base):
    __tablename__ = "flag_submissions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    challenge_id: Mapped[int] = mapped_column(ForeignKey("challenges.id"), nullable=False)
    submitted_flag: Mapped[str] = mapped_column(String(128), nullable=False)
    is_correct: Mapped[bool] = mapped_column(Boolean, nullable=False)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=dt.datetime.utcnow)


class PatchSubmission(Base):
    __tablename__ = "patch_submissions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    challenge_id: Mapped[int] = mapped_column(ForeignKey("challenges.id"), nullable=False)
    patch_content: Mapped[str] = mapped_column(String(5000), nullable=False)
    is_successful: Mapped[bool] = mapped_column(Boolean, nullable=False)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=dt.datetime.utcnow)


class ScoreEvent(Base):
    __tablename__ = "score_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), nullable=False, index=True)
    challenge_id: Mapped[int] = mapped_column(ForeignKey("challenges.id"), nullable=False)
    points: Mapped[int] = mapped_column(Integer, nullable=False)
    reason: Mapped[str] = mapped_column(String(32), nullable=False)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=dt.datetime.utcnow)
