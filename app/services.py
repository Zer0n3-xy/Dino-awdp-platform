import secrets

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import (
    Challenge,
    DynamicContainer,
    FlagSubmission,
    PatchSubmission,
    ScoreEvent,
    Team,
    TeamMember,
    User,
)


def ensure_default_challenges(db: Session) -> None:
    exists = db.scalar(select(func.count(Challenge.id)))
    if exists:
        return
    db.add_all(
        [
            Challenge(
                name="web-login-rce",
                flag="DINO{demo_flag_1}",
                score_flag=100,
                score_patch=150,
                vulnerability_signature="FIXED",
            ),
            Challenge(
                name="api-ssrf",
                flag="DINO{demo_flag_2}",
                score_flag=120,
                score_patch=180,
                vulnerability_signature="SAFE_GUARD",
            ),
        ]
    )
    db.commit()


def create_team_and_join(db: Session, user: User, team_name: str) -> Team:
    if db.scalar(select(Team).where(Team.name == team_name)):
        raise HTTPException(status_code=400, detail="Team name already exists")

    team = Team(name=team_name, invite_code=secrets.token_hex(4), created_by=user.id)
    db.add(team)
    db.flush()
    db.add(TeamMember(user_id=user.id, team_id=team.id, is_captain=True))
    db.commit()
    db.refresh(team)
    return team


def join_team_by_invite(db: Session, user: User, invite_code: str) -> Team:
    team = db.scalar(select(Team).where(Team.invite_code == invite_code))
    if not team:
        raise HTTPException(status_code=404, detail="Invalid invite code")

    exists = db.scalar(select(TeamMember).where(TeamMember.user_id == user.id, TeamMember.team_id == team.id))
    if exists:
        return team

    db.add(TeamMember(user_id=user.id, team_id=team.id, is_captain=False))
    db.commit()
    return team


def get_user_team(db: Session, user_id: int) -> Team:
    membership = db.scalar(select(TeamMember).where(TeamMember.user_id == user_id))
    if not membership:
        raise HTTPException(status_code=400, detail="User is not in any team")
    team = db.get(Team, membership.team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    return team


def allocate_container(db: Session, team_id: int, challenge: Challenge) -> DynamicContainer:
    endpoint = f"http://team-{team_id}-challenge-{challenge.id}.arena.local"
    container = DynamicContainer(team_id=team_id, challenge_id=challenge.id, endpoint=endpoint, status="running")
    db.add(container)
    db.commit()
    db.refresh(container)
    return container


def process_flag_submission(db: Session, user_id: int, team_id: int, challenge: Challenge, flag: str):
    already_solved = db.scalar(
        select(ScoreEvent).where(
            ScoreEvent.team_id == team_id,
            ScoreEvent.challenge_id == challenge.id,
            ScoreEvent.reason == "flag",
        )
    )
    is_correct = flag == challenge.flag

    db.add(
        FlagSubmission(
            team_id=team_id,
            user_id=user_id,
            challenge_id=challenge.id,
            submitted_flag=flag,
            is_correct=is_correct,
        )
    )

    points = 0
    if is_correct and not already_solved:
        points = challenge.score_flag
        db.add(ScoreEvent(team_id=team_id, challenge_id=challenge.id, points=points, reason="flag"))

    db.commit()
    return is_correct, points


def check_patch_success(challenge: Challenge, patch_content: str) -> bool:
    keyword_ok = challenge.vulnerability_signature in patch_content
    bypass_sign = "BYPASS" in patch_content
    return keyword_ok and not bypass_sign


def process_patch_submission(db: Session, user_id: int, team_id: int, challenge: Challenge, patch_content: str):
    successful = check_patch_success(challenge, patch_content)
    already_patched = db.scalar(
        select(ScoreEvent).where(
            ScoreEvent.team_id == team_id,
            ScoreEvent.challenge_id == challenge.id,
            ScoreEvent.reason == "patch",
        )
    )

    db.add(
        PatchSubmission(
            team_id=team_id,
            user_id=user_id,
            challenge_id=challenge.id,
            patch_content=patch_content,
            is_successful=successful,
        )
    )

    points = 0
    if successful and not already_patched:
        points = challenge.score_patch
        db.add(ScoreEvent(team_id=team_id, challenge_id=challenge.id, points=points, reason="patch"))

    db.commit()
    return successful, points


def calculate_leaderboard(db: Session):
    rows = db.execute(
        select(Team.id, Team.name, func.coalesce(func.sum(ScoreEvent.points), 0))
        .join(ScoreEvent, ScoreEvent.team_id == Team.id, isouter=True)
        .group_by(Team.id, Team.name)
        .order_by(func.coalesce(func.sum(ScoreEvent.points), 0).desc(), Team.id.asc())
    ).all()
    return rows
