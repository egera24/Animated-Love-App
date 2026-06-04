from pydantic import BaseModel


class LoginRequest(BaseModel):
    password: str


class LoginResponse(BaseModel):
    ok: bool
    message: str


class WeatherInfo(BaseModel):
    city: str
    temp_c: float | None
    description_hu: str
    weather_code: int
    mood_hint: str


class ContentSnippet(BaseModel):
    module: str
    text: str
    title: str | None = None


class TodayResponse(BaseModel):
    mood: str
    bubble_text: str
    hedgehog_name: str
    recipient_name: str
    is_birthday: bool
    is_special_date: bool
    special_date_label: str | None
    weather: WeatherInfo | None
    language: str
    poem: ContentSnippet | None = None
    book_tip: ContentSnippet | None = None
    movie_tip: ContentSnippet | None = None


class ContentModuleResponse(BaseModel):
    module: str
    text: str
    title: str | None = None
    source: str = "corpus"


class MediaItemOut(BaseModel):
    id: int
    filename: str
    original_name: str
    url: str
    uploaded_by: str
    created_at: str


class MediaListResponse(BaseModel):
    items: list[MediaItemOut]
    total: int
    page: int
    limit: int
