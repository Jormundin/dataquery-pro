from pydantic import BaseModel
from typing import List, Dict, Optional, Any
from datetime import datetime

# Request Models
class QueryRequest(BaseModel):
    database_id: str
    table: str
    columns: Optional[List[str]] = None
    filters: Optional[List[Dict[str, Any]]] = None
    sort_by: Optional[str] = None
    sort_order: Optional[str] = "ASC"
    limit: Optional[int] = 100

class ConnectionTestRequest(BaseModel):
    host: str
    port: str
    sid: str
    username: str
    password: str

class SaveQueryRequest(BaseModel):
    name: str
    description: Optional[str] = None
    sql: str
    database_id: str
    table: str

class DataRequest(BaseModel):
    table: str
    page: Optional[int] = 1
    limit: Optional[int] = 25
    search: Optional[str] = None
    sort_by: Optional[str] = None
    sort_order: Optional[str] = "asc"
    filters: Optional[Dict[str, Any]] = None

# Response Models
class DatabaseResponse(BaseModel):
    id: str
    name: str
    description: str
    status: str

class TableResponse(BaseModel):
    name: str
    description: str
    columns_count: int

class ColumnResponse(BaseModel):
    name: str
    type: str
    description: str

class ConnectionTestResponse(BaseModel):
    status: str
    message: str
    connected: bool

class QueryResultResponse(BaseModel):
    success: bool
    columns: Optional[List[str]] = None
    data: Optional[List[Dict[str, Any]]] = None
    row_count: Optional[int] = None
    message: str
    execution_time: Optional[str] = None
    error: Optional[str] = None

class SavedQueryResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    sql: str
    database_id: str
    table: str
    created_at: datetime
    updated_at: Optional[datetime] = None

class DataResponse(BaseModel):
    data: List[Dict[str, Any]]
    total_count: int
    page: int
    limit: int
    total_pages: int

class StatsResponse(BaseModel):
    total_queries: int
    active_databases: int
    total_users: int
    avg_response_time: str

class QueryHistoryResponse(BaseModel):
    id: int
    sql: str
    database_id: str
    table: str
    execution_time: str
    status: str
    created_at: datetime
    row_count: Optional[int] = None

# Settings Models
class DatabaseSettings(BaseModel):
    host: str
    port: str
    database: str
    username: str
    ssl: bool = False
    connection_timeout: int = 30

class APISettings(BaseModel):
    base_url: str
    timeout: int = 30000
    retries: int = 3
    api_key: Optional[str] = None

class UserPreferences(BaseModel):
    default_rows_per_page: int = 25
    date_format: str = "dd.MM.yyyy"
    timezone: str = "Europe/Moscow"
    theme: str = "light"
    auto_refresh: bool = False
    refresh_interval: int = 30

class SettingsResponse(BaseModel):
    database: DatabaseSettings
    api: APISettings
    preferences: UserPreferences

class ErrorResponse(BaseModel):
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None 