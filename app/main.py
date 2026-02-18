from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import create_access_token, get_password_hash, verify_password
from app.database import Base, SessionLocal, engine, get_db
from app.deps import get_current_user
from app.models import Challenge, User
from app.schemas import (
    ChallengeResponse,
    ContainerAllocateRequest,
    ContainerResponse,
    FlagSubmitRequest,
    JudgeResponse,
    LeaderboardItem,
    LoginRequest,
    PatchSubmitRequest,
    RegisterRequest,
    TeamCreateRequest,
    TeamResponse,
    TokenResponse,
)
from app.services import (
    allocate_container,
    calculate_leaderboard,
    create_team_and_join,
    ensure_default_challenges,
    get_user_team,
    join_team_by_invite,
    process_flag_submission,
    process_patch_submission,
)

app = FastAPI(title=settings.app_name)


@app.on_event("startup")
def startup() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        ensure_default_challenges(db)
    finally:
        db.close()


@app.post("/auth/register", response_model=TokenResponse)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.username == payload.username))
    if user:
        raise HTTPException(status_code=400, detail="Username already exists")

    created = User(username=payload.username, password_hash=get_password_hash(payload.password))
    db.add(created)
    db.commit()
    token = create_access_token(subject=created.username)
    return TokenResponse(access_token=token)


@app.post("/auth/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.username == payload.username))
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    token = create_access_token(subject=user.username)
    return TokenResponse(access_token=token)


@app.post("/teams", response_model=TeamResponse)
def create_team(
    payload: TeamCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    team = create_team_and_join(db, current_user, payload.name)
    return TeamResponse(id=team.id, name=team.name, invite_code=team.invite_code)


@app.post("/teams/{invite_code}/join", response_model=TeamResponse)
def join_team(
    invite_code: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    team = join_team_by_invite(db, current_user, invite_code)
    return TeamResponse(id=team.id, name=team.name, invite_code=team.invite_code)


@app.get("/challenges", response_model=list[ChallengeResponse])
def list_challenges(db: Session = Depends(get_db)):
    items = db.scalars(select(Challenge).order_by(Challenge.id.asc())).all()
    return [
        ChallengeResponse(
            id=item.id,
            name=item.name,
            score_flag=item.score_flag,
            score_patch=item.score_patch,
        )
        for item in items
    ]


@app.post("/containers/allocate", response_model=ContainerResponse)
def create_container(
    payload: ContainerAllocateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    team = get_user_team(db, current_user.id)
    challenge = db.get(Challenge, payload.challenge_id)
    if not challenge:
        raise HTTPException(status_code=404, detail="Challenge not found")
    container = allocate_container(db, team.id, challenge)
    return ContainerResponse(endpoint=container.endpoint, status=container.status)


@app.post("/flags/submit", response_model=JudgeResponse)
def submit_flag(
    payload: FlagSubmitRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    team = get_user_team(db, current_user.id)
    challenge = db.get(Challenge, payload.challenge_id)
    if not challenge:
        raise HTTPException(status_code=404, detail="Challenge not found")

    success, points = process_flag_submission(db, current_user.id, team.id, challenge, payload.flag)
    return JudgeResponse(
        success=success,
        message="Flag correct" if success else "Flag incorrect",
        awarded_points=points,
    )


@app.post("/patches/submit", response_model=JudgeResponse)
def submit_patch(
    payload: PatchSubmitRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    team = get_user_team(db, current_user.id)
    challenge = db.get(Challenge, payload.challenge_id)
    if not challenge:
        raise HTTPException(status_code=404, detail="Challenge not found")

    success, points = process_patch_submission(
        db,
        current_user.id,
        team.id,
        challenge,
        payload.patch_content,
    )
    return JudgeResponse(
        success=success,
        message="Patch accepted" if success else "Patch rejected",
        awarded_points=points,
    )


@app.get("/leaderboard", response_model=list[LeaderboardItem])
def leaderboard(db: Session = Depends(get_db)):
    rows = calculate_leaderboard(db)
    return [LeaderboardItem(team_id=tid, team_name=name, score=score) for tid, name, score in rows]
