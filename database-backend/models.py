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
    client_id: Optional[str] = None  # For progress tracking

class QueryRequestLarge(BaseModel):
    """Extended query request for large datasets with memory management options"""
    database_id: str
    table: str
    columns: Optional[List[str]] = None
    filters: Optional[List[Dict[str, Any]]] = None
    sort_by: Optional[str] = None
    sort_order: Optional[str] = "ASC"
    limit: Optional[int] = 100
    # Memory management options
    enable_chunking: Optional[bool] = True
    chunk_size: Optional[int] = 5000
    max_memory_rows: Optional[int] = 50000

class StratificationRequest(BaseModel):
    """Request model for stratification with memory management"""
    query_data: Dict[str, Any]
    stratification_config: Dict[str, Any]
    # Memory management settings
    max_memory_rows: Optional[int] = 500000
    sample_size: Optional[int] = 100000
    use_sampling: Optional[bool] = True

class ConnectionTestRequest(BaseModel):
    host: Optional[str] = None
    port: Optional[int] = None
    database: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None

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

# Authentication Models
class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user: Dict[str, Any]
    expires_in: int

class UserResponse(BaseModel):
    username: str
    name: str
    role: str
    permissions: List[str]

# Response Models
class DatabaseResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None

class TableResponse(BaseModel):
    name: str
    description: Optional[str] = None
    columns_count: Optional[int] = None

class ColumnResponse(BaseModel):
    name: str
    type: str
    description: Optional[str] = None
    nullable: Optional[bool] = True
    options: Optional[List[str]] = None

class MemoryInfo(BaseModel):
    """Memory usage information for large datasets"""
    total_rows: int
    memory_efficient_processing: bool
    chunked_processing: bool
    estimated_memory_mb: Optional[float] = None
    warnings: Optional[List[str]] = None

class QueryResultResponse(BaseModel):
    success: bool
    columns: Optional[List[str]] = None
    data: Optional[List[Dict[str, Any]]] = None
    row_count: Optional[int] = None
    message: Optional[str] = None
    error: Optional[str] = None
    execution_time: Optional[str] = None
    memory_info: Optional[MemoryInfo] = None
    temp_file_id: Optional[str] = None

class QueryHistoryResponse(BaseModel):
    id: int
    sql: str
    database_id: str
    table: str
    execution_time: str
    status: str
    created_at: datetime
    row_count: int
    user: Optional[str] = None

class SavedQueryResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    sql: str
    database_id: str
    table: str
    created_at: datetime
    updated_at: Optional[datetime] = None

class ConnectionTestResponse(BaseModel):
    status: str
    message: str
    connected: bool
    response_time: Optional[str] = None

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

# Settings Models
class DatabaseSettings(BaseModel):
    host: str
    port: str
    database: str
    username: str
    ssl: bool = False
    connection_timeout: int = 300

class APISettings(BaseModel):
    base_url: str
    timeout: int = 300000
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

# Theory Management Models
class CreateTheoryRequest(BaseModel):
    theory_name: str
    theory_description: str
    theory_start_date: str  # YYYY-MM-DD format
    theory_end_date: str    # YYYY-MM-DD format
    user_iins: List[str]    # List of IIN values from query results

class TheoryResponse(BaseModel):
    theory_id: str  # Changed from int to str to support decimal IDs like "1.1"
    theory_name: str
    theory_description: str
    load_date: str
    theory_start_date: str
    theory_end_date: str
    user_count: int
    is_active: bool
    created_by: str

class TheoryCreateResponse(BaseModel):
    success: bool
    message: str
    theory_id: Optional[str] = None  # Changed from int to str to support decimal IDs
    users_added: Optional[int] = None

class StratificationResponse(BaseModel):
    """Response model for stratification operations"""
    success: bool
    n_splits: int
    stratify_cols: List[str]
    stratified_groups: List[Dict[str, Any]]
    total_rows: int
    message: str
    memory_info: Optional[MemoryInfo] = None
    iteration_info: Optional[Dict[str, Any]] = None 