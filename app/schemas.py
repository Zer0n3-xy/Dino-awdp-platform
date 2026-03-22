from pydantic import BaseModel, Field


class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=32)
    password: str = Field(min_length=6, max_length=128)


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class CompetitionCreateRequest(BaseModel):
    name: str = Field(min_length=2, max_length=128)
    description: str = Field(default="", max_length=1024)


class CompetitionResponse(BaseModel):
    id: int
    name: str
    description: str


class TeamCreateRequest(BaseModel):
    name: str = Field(min_length=2, max_length=64)


class TeamResponse(BaseModel):
    id: int
    name: str
    invite_code: str


class ChallengeResponse(BaseModel):
    id: int
    name: str
    score_flag: int
    score_patch: int


class ContainerAllocateRequest(BaseModel):
    challenge_id: int


class ContainerResponse(BaseModel):
    endpoint: str
    status: str


class FlagSubmitRequest(BaseModel):
    challenge_id: int
    flag: str = Field(min_length=1, max_length=128)


class PatchSubmitRequest(BaseModel):
    challenge_id: int
    patch_content: str = Field(min_length=1, max_length=5000)


class JudgeResponse(BaseModel):
    success: bool
    message: str
    awarded_points: int = 0


class LeaderboardItem(BaseModel):
    team_id: int
    team_name: str
    score: int
