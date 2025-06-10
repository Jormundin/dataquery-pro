import os
import time
import io
import csv
import math
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query, Response, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv

from models import *
from database import (
    get_databases, get_tables, get_table_columns, 
    test_connection, execute_query
)
from query_builder import QueryBuilder
from auth import authenticate_user, create_access_token, get_current_user, ACCESS_TOKEN_EXPIRE_MINUTES
from stratification import stratify_data

# Load environment variables
load_dotenv()

# Initialize FastAPI app
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    yield
    # Shutdown
    pass

app = FastAPI(
    title="DataQuery Pro API",
    description="Корпоративный API интерфейс для работы с Oracle базой данных",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# Initialize query builder
query_builder = QueryBuilder()

# In-memory storage for demo purposes
query_history = []
saved_queries = []
app_settings = {
    "database": {
        "host": os.getenv("ORACLE_HOST", ""),
        "port": os.getenv("ORACLE_PORT", "1521"),
        "database": os.getenv("ORACLE_SID", ""),
        "username": os.getenv("ORACLE_USER", ""),
        "ssl": False,
        "connection_timeout": 30
    },
    "api": {
        "base_url": "http://172.28.80.18:1555",
        "timeout": 30000,
        "retries": 3,
        "api_key": ""
    },
    "preferences": {
        "default_rows_per_page": 25,
        "date_format": "dd.MM.yyyy",
        "timezone": "Europe/Moscow",
        "theme": "light",
        "auto_refresh": False,
        "refresh_interval": 30
    }
}

def get_current_user_dependency(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Dependency to get current authenticated user"""
    token = credentials.credentials
    return get_current_user(token)

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "DataQuery Pro API", 
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "authentication": "LDAP enabled"
    }

# Health check
@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

# Authentication endpoints
@app.post("/auth/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """LDAP Authentication Login"""
    try:
        user_info = authenticate_user(request.username, request.password)
        
        # Create access token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user_info["username"]}, 
            expires_delta=access_token_expires
        )
        
        return LoginResponse(
            access_token=access_token,
            token_type="bearer",
            user=user_info,
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60  # in seconds
        )
        
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Authentication error: {str(e)}"
        )

@app.get("/auth/me", response_model=UserResponse)
async def get_current_user_info(current_user: dict = Depends(get_current_user_dependency)):
    """Get current authenticated user information"""
    return UserResponse(**current_user)

@app.post("/auth/logout")
async def logout():
    """Logout (client-side token removal)"""
    return {"message": "Successfully logged out"}

# Protected Database endpoints
@app.get("/databases", response_model=List[DatabaseResponse])
async def list_databases(current_user: dict = Depends(get_current_user_dependency)):
    """Получить список доступных баз данных"""
    try:
        databases = get_databases()
        return databases
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения списка БД: {str(e)}")

@app.get("/databases/{database_id}/tables", response_model=List[TableResponse])
async def list_tables(database_id: str, current_user: dict = Depends(get_current_user_dependency)):
    """Получить список таблиц для базы данных"""
    try:
        tables = get_tables(database_id.upper())
        return tables
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения списка таблиц: {str(e)}")

@app.get("/databases/{database_id}/tables/{table_name}/columns", response_model=List[ColumnResponse])
async def list_columns(database_id: str, table_name: str, current_user: dict = Depends(get_current_user_dependency)):
    """Получить список столбцов для таблицы"""
    try:
        columns = get_table_columns(database_id.upper(), table_name.upper())
        return columns
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения столбцов: {str(e)}")

@app.post("/databases/test-connection", response_model=ConnectionTestResponse)
async def test_db_connection(request: Optional[ConnectionTestRequest] = None, current_user: dict = Depends(get_current_user_dependency)):
    """Тестирование подключения к базе данных"""
    try:
        result = test_connection()
        return result
    except Exception as e:
        return {
            "status": "error",
            "message": f"Ошибка тестирования соединения: {str(e)}",
            "connected": False
        }

# Protected Query endpoints
@app.post("/query/execute", response_model=QueryResultResponse)
async def execute_database_query(request: QueryRequest, current_user: dict = Depends(get_current_user_dependency)):
    """Выполнение запроса к базе данных"""
    try:
        start_time = time.time()
        
        # Build safe SQL query
        request_data = request.dict()
        sql_query = query_builder.build_query(request_data)
        
        # Execute query
        result = execute_query(sql_query)
        
        execution_time = f"{(time.time() - start_time):.3f}s"
        
        if result["success"]:
            # Add to query history with user info
            # Get next ID (max existing ID + 1)
            next_id = max([q.get("id", 0) for q in query_history], default=0) + 1
            
            query_history.append({
                "id": next_id,
                "sql": sql_query,
                "database_id": request.database_id,
                "table": request.table,
                "execution_time": execution_time,
                "status": "success",
                "created_at": datetime.now(),
                "row_count": result["row_count"],
                "user": current_user["username"]
            })
            
            return QueryResultResponse(
                success=True,
                columns=result["columns"],
                data=result["data"],
                row_count=result["row_count"],
                message=result["message"],
                execution_time=execution_time
            )
        else:
            # Add failed query to history
            # Get next ID (max existing ID + 1)
            next_id = max([q.get("id", 0) for q in query_history], default=0) + 1
            
            query_history.append({
                "id": next_id,
                "sql": sql_query,
                "database_id": request.database_id,
                "table": request.table,
                "execution_time": execution_time,
                "status": "error",
                "created_at": datetime.now(),
                "row_count": 0,
                "user": current_user["username"]
            })
            
            return QueryResultResponse(
                success=False,
                message=result["message"],
                error=result["error"],
                execution_time=execution_time
            )
            
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка выполнения запроса: {str(e)}")

@app.post("/query/count")
async def get_query_count(request: QueryRequest, current_user: dict = Depends(get_current_user_dependency)):
    """Получить количество строк для запроса с фильтрами"""
    try:
        start_time = time.time()
        
        # Build count SQL query
        request_data = request.dict()
        count_query = query_builder.build_count_query(request_data)
        
        # Execute count query
        result = execute_query(count_query)
        
        execution_time = f"{(time.time() - start_time):.3f}s"
        
        if result["success"] and result["data"]:
            # Extract count from result
            count = 0
            if result["data"]:
                # Handle different possible column names for count
                first_row = result["data"][0]
                for key, value in first_row.items():
                    if isinstance(value, (int, float)):
                        count = int(value)
                        break
            
            return {
                "success": True,
                "count": count,
                "execution_time": execution_time,
                "query": count_query
            }
        else:
            return {
                "success": False,
                "count": 0,
                "message": result.get("message", "Ошибка выполнения запроса подсчета"),
                "error": result.get("error", ""),
                "execution_time": execution_time
            }
            
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения количества строк: {str(e)}")

# Theory Management endpoints
@app.post("/theories/create", response_model=TheoryCreateResponse)
async def create_theory_endpoint(request: CreateTheoryRequest, current_user: dict = Depends(get_current_user_dependency)):
    """Создать новую теорию с пользователями"""
    # Check permissions - only users with 'write' or 'admin' permissions can create theories
    if 'write' not in current_user.get('permissions', []) and 'admin' not in current_user.get('permissions', []):
        raise HTTPException(
            status_code=403,
            detail="Недостаточно прав для создания теорий"
        )
    
    try:
        from database import create_theory
        
        result = create_theory(
            request.theory_name,
            request.theory_description,
            request.theory_start_date,
            request.theory_end_date,
            request.user_iins,
            current_user["username"]
        )
        
        return TheoryCreateResponse(**result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка создания теории: {str(e)}")

@app.get("/theories/active", response_model=List[TheoryResponse])
async def get_active_theories_endpoint(current_user: dict = Depends(get_current_user_dependency)):
    """Получить список всех теорий"""
    try:
        from database import get_active_theories
        
        result = get_active_theories()
        
        if result["success"]:
            return result["data"]
        else:
            raise HTTPException(status_code=500, detail=result["message"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения теорий: {str(e)}")

@app.post("/theories/detect-iins")
async def detect_iins_in_results(data: Dict[str, Any], current_user: dict = Depends(get_current_user_dependency)):
    """Обнаружить IIN колонки в результатах запроса"""
    try:
        from database import detect_iin_columns, extract_iin_values
        
        query_results = data.get("results", [])
        
        if not query_results:
            return {
                "has_iin_column": False,
                "iin_column": None,
                "iin_values": [],
                "user_count": 0
            }
        
        iin_column = detect_iin_columns(query_results)
        
        if iin_column:
            iin_values = extract_iin_values(query_results, iin_column)
            return {
                "has_iin_column": True,
                "iin_column": iin_column,
                "iin_values": iin_values,
                "user_count": len(iin_values)
            }
        else:
            return {
                "has_iin_column": False,
                "iin_column": None,
                "iin_values": [],
                "user_count": 0
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка анализа результатов: {str(e)}")

@app.post("/theories/stratify-and-create")
async def stratify_and_create_theories(data: Dict[str, Any], current_user: dict = Depends(get_current_user_dependency)):
    """Стратификация данных и создание нескольких теорий"""
    try:
        query_data = data.get("queryData")
        stratification_config = data.get("stratificationConfig")
        
        if not query_data or not stratification_config:
            raise HTTPException(status_code=400, detail="Отсутствуют данные запроса или конфигурация стратификации")

        # First execute the query to get the data
        start_time = time.time()
        
        try:
            sql_query = query_builder.build_query(query_data)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Ошибка построения SQL запроса: {str(e)}")
        
        try:
            result = execute_query(sql_query)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Ошибка выполнения запроса: {str(e)}")
        
        if not result["success"]:
            raise HTTPException(status_code=500, detail=f"Ошибка выполнения запроса: {result['message']}")
        
        if not result["data"]:
            raise HTTPException(status_code=400, detail="Запрос не возвратил данных для стратификации")
        
        # Check if required dependencies are available
        try:
            import pandas as pd
            import numpy as np
            from sklearn.model_selection import StratifiedKFold
            from scipy.stats import ks_2samp
        except ImportError as e:
            raise HTTPException(status_code=500, detail=f"Отсутствует зависимость для стратификации: {str(e)}")

        # Prepare data for stratification
        stratification_request = {
            "data": result["data"],
            "columns": result["columns"],
            "n_splits": stratification_config.get("numGroups", 2),
            "stratify_cols": stratification_config.get("stratifyColumns", []),
            "replace_nan": True,
            "random_state": stratification_config.get("randomSeed", 42)
        }
        
        # Check for case sensitivity issues and fix column names
        actual_columns = stratification_request['columns']
        requested_stratify_cols = stratification_request['stratify_cols']
        
        # Create a case-insensitive mapping
        column_mapping = {}
        for actual_col in actual_columns:
            for requested_col in requested_stratify_cols:
                if actual_col.upper() == requested_col.upper():
                    column_mapping[requested_col] = actual_col
                    break
        
        # Update stratify_cols with the actual column names
        fixed_stratify_cols = []
        for requested_col in requested_stratify_cols:
            if requested_col in column_mapping:
                fixed_stratify_cols.append(column_mapping[requested_col])
            else:
                raise HTTPException(status_code=400, detail=f"Колонка '{requested_col}' не найдена. Доступные колонки: {actual_columns}")
        
        # Update the stratification request with corrected column names
        stratification_request['stratify_cols'] = fixed_stratify_cols

        # Also fix the IIN column name
        iin_column = stratification_config.get("iinColumn")
        if iin_column:
            for actual_col in actual_columns:
                if actual_col.upper() == iin_column.upper():
                    # Update the config for later use
                    stratification_config["iinColumn"] = actual_col
                    break

        # Call local stratification function
        try:
            from stratification import stratify_data
            stratification_result = stratify_data(stratification_request)
        except ImportError as e:
            raise HTTPException(status_code=500, detail=f"Ошибка импорта модуля стратификации: {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Ошибка стратификации: {str(e)}")
        
        # Create theories for each stratified group
        try:
            from database import create_theory_with_custom_id, get_next_theory_id
        except ImportError as e:
            raise HTTPException(status_code=500, detail=f"Ошибка импорта функций создания теории: {str(e)}")
        
        # Get base theory ID for this stratification
        base_theory_id = get_next_theory_id()
        
        created_theories = []
        
        for i, group in enumerate(stratification_result.get("stratified_groups", [])):
            group_letter = chr(65 + i)  # A, B, C, D, E
            
            # Extract IIN values from the group data
            iin_column = stratification_config.get("iinColumn")
            iin_values = []
            
            if iin_column:
                for row in group.get("data", []):
                    if iin_column in row and row[iin_column]:
                        iin_values.append(str(row[iin_column]))
            
            # Create theory data
            theory_name = f"{stratification_config.get('theoryBaseName', 'Стратифицированная теория')} - Группа {group_letter}"
            theory_description = f"{stratification_config.get('theoryDescription', 'Теория создана через стратификацию данных')} (Группа {group_letter} - {group.get('num_rows', 0)} записей, пропорция: {group.get('proportion', 0):.3f})"
            theory_start_date = stratification_config.get("theoryStartDate")
            theory_end_date = stratification_config.get("theoryEndDate")
            created_by = current_user["username"]
            
            # Create sub-ID for this group (e.g., 1.1, 1.2, 1.3)
            sub_theory_id = f"{base_theory_id}.{i + 1}"
            
            # Insert theory using custom ID function
            try:
                theory_result = create_theory_with_custom_id(
                    theory_name,
                    theory_description,
                    theory_start_date,
                    theory_end_date,
                    iin_values,
                    created_by,
                    sub_theory_id
                )
                
                if theory_result.get("success"):
                    created_theories.append({
                        "theory_id": theory_result.get("theory_id"),
                        "theory_name": theory_name,
                        "users_added": theory_result.get("users_added", 0),
                        "group": group_letter,
                        "proportion": group.get("proportion", 0),
                        "num_rows": group.get("num_rows", 0),
                        "sub_id": sub_theory_id
                    })
                else:
                    continue
                    
            except Exception as e:
                # Continue with other groups even if one fails
                continue
        
        if not created_theories:
            raise HTTPException(status_code=500, detail="Не удалось создать ни одной теории")
        
        execution_time = time.time() - start_time
        
        return {
            "success": True,
            "message": f"Успешно создано {len(created_theories)} теорий через стратификацию с базовым ID {base_theory_id}",
            "stratification": stratification_result,
            "theories": created_theories,
            "execution_time": f"{execution_time:.3f}s",
            "total_users": sum(theory["users_added"] for theory in created_theories),
            "base_theory_id": base_theory_id
        }
        
    except HTTPException as he:
        # Re-raise HTTP exceptions as-is
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Неожиданная ошибка стратификации: {str(e)}")

# Remaining endpoints with authentication protection...
@app.get("/query/history", response_model=List[QueryHistoryResponse])
async def get_query_history(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    current_user: dict = Depends(get_current_user_dependency)
):
    """Получить историю запросов"""
    start_idx = (page - 1) * limit
    end_idx = start_idx + limit
    
    # Sort by most recent first
    sorted_history = sorted(query_history, key=lambda x: x["created_at"], reverse=True)
    paginated_history = sorted_history[start_idx:end_idx]
    
    return paginated_history

@app.post("/query/save", response_model=SavedQueryResponse)
async def save_query(request: SaveQueryRequest, current_user: dict = Depends(get_current_user_dependency)):
    """Сохранить запрос"""
    saved_query = {
        "id": len(saved_queries) + 1,
        "name": request.name,
        "description": request.description,
        "sql": request.sql,
        "database_id": request.database_id,
        "table": request.table,
        "created_at": datetime.now(),
        "updated_at": None,
        "user": current_user["username"]
    }
    
    saved_queries.append(saved_query)
    return saved_query

@app.get("/query/saved", response_model=List[SavedQueryResponse])
async def get_saved_queries(current_user: dict = Depends(get_current_user_dependency)):
    """Получить сохраненные запросы"""
    return saved_queries

@app.delete("/query/saved/{query_id}")
async def delete_saved_query(query_id: int, current_user: dict = Depends(get_current_user_dependency)):
    """Удалить сохраненный запрос"""
    global saved_queries
    saved_queries = [q for q in saved_queries if q["id"] != query_id]
    return {"message": "Запрос удален"}

# Protected Data endpoints
@app.get("/data", response_model=DataResponse)
async def get_data(
    database_id: str = Query(..., description="Database ID"),
    table: str = Query(..., description="Table name"),
    page: int = Query(1, ge=1),
    limit: int = Query(100, ge=1, le=500), # Increased default and max limit for better performance
    search: Optional[str] = Query(None),
    sort_by: Optional[str] = Query(None),
    sort_order: str = Query("asc"),
    current_user: dict = Depends(get_current_user_dependency)
):
    """Получить данные с фильтрами и пагинацией - оптимизированная версия для больших датасетов"""
    try:
        from database import get_table_columns
        
        # Build WHERE clause for search
        where_conditions = []
        query_params = {}
        
        if search:
            # Get actual table columns for search
            table_columns = get_table_columns(database_id.upper(), table)
            text_columns = [col['name'] for col in table_columns 
                          if col['type'].upper() in ['VARCHAR2', 'CHAR', 'CLOB']]
            
            # Create search conditions for text columns (limit to first 3 to avoid overly complex queries)
            search_conditions = []
            for i, col in enumerate(text_columns[:3]):
                param_name = f"search_param_{i}"
                search_conditions.append(f"UPPER({col}) LIKE UPPER(:{param_name})")
                query_params[param_name] = f"%{search}%"
            
            if search_conditions:
                where_conditions.append(f"({' OR '.join(search_conditions)})")
        
        # Build WHERE clause
        where_clause = ""
        if where_conditions:
            where_clause = f"WHERE {' AND '.join(where_conditions)}"
        
        # Build ORDER BY clause
        order_clause = ""
        if sort_by:
            sort_direction = "DESC" if sort_order.upper() == "DESC" else "ASC"
            order_clause = f"ORDER BY {sort_by} {sort_direction}"
        
        # Step 1: Get total count efficiently
        count_query = f"SELECT COUNT(*) as total_count FROM {table.upper()} {where_clause}"
        count_result = execute_query(count_query, query_params)
        
        total_count = 0
        if count_result["success"] and count_result["data"]:
            total_count = count_result["data"][0].get("total_count", 0)
        
        # Step 2: Get paginated data using Oracle ROWNUM pagination
        offset = (page - 1) * limit
        
        # Oracle pagination query using ROWNUM
        paginated_query = f"""
        SELECT * FROM (
            SELECT a.*, ROWNUM rnum FROM (
                SELECT * FROM {table.upper()} 
                {where_clause}
                {order_clause}
            ) a 
            WHERE ROWNUM <= {offset + limit}
        ) 
        WHERE rnum > {offset}
        """
        
        data_result = execute_query(paginated_query, query_params)
        
        if data_result["success"]:
            # Remove the 'rnum' column from results
            cleaned_data = []
            for row in data_result["data"]:
                cleaned_row = {k: v for k, v in row.items() if k.lower() != 'rnum'}
                cleaned_data.append(cleaned_row)
            
            total_pages = math.ceil(total_count / limit) if total_count > 0 else 1
            
            return DataResponse(
                data=cleaned_data,
                total_count=total_count,
                page=page,
                limit=limit,
                total_pages=total_pages
            )
        else:
            raise HTTPException(status_code=500, detail=data_result["message"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения данных: {str(e)}")

@app.get("/data/export")
async def export_data(
    database_id: str = Query(..., description="Database ID"),
    table: str = Query(..., description="Table name"),
    format: str = Query("csv", description="Export format"),
    current_user: dict = Depends(get_current_user_dependency)
):
    """Экспорт данных"""
    try:
        request_data = {
            "database_id": database_id.upper(),
            "table": table,
            "limit": 10000  # Max export limit
        }
        
        sql_query = query_builder.build_query(request_data)
        result = execute_query(sql_query)
        
        if not result["success"]:
            raise HTTPException(status_code=500, detail=result["message"])
        
        if format.lower() == "csv":
            # Generate CSV
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write headers
            if result["columns"]:
                writer.writerow(result["columns"])
            
            # Write data
            for row in result["data"]:
                if result["columns"]:
                    row_values = [row.get(col, "") for col in result["columns"]]
                    writer.writerow(row_values)
            
            # Prepare response
            csv_content = output.getvalue()
            output.close()
            
            response = Response(
                content=csv_content,
                media_type="text/csv",
                headers={"Content-Disposition": f"attachment; filename={table}_export.csv"}
            )
            return response
        
        else:
            raise HTTPException(status_code=400, detail="Неподдерживаемый формат экспорта")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка экспорта: {str(e)}")

@app.get("/data/stats/{table_name}")
async def get_data_stats(table_name: str, database_id: str = Query("dssb_app"), current_user: dict = Depends(get_current_user_dependency)):
    """Получить статистику данных"""
    try:
        # Get table row count
        count_query = f"SELECT COUNT(*) as total_rows FROM {table_name.upper()}"
        result = execute_query(count_query)
        
        if result["success"] and result["data"]:
            total_rows = result["data"][0].get("total_rows", 0)
            return {
                "table_name": table_name,
                "total_rows": total_rows,
                "last_updated": datetime.now().isoformat()
            }
        else:
            raise HTTPException(status_code=500, detail="Ошибка получения статистики")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения статистики: {str(e)}")

# Protected Settings endpoints
@app.get("/settings", response_model=SettingsResponse)
async def get_settings(current_user: dict = Depends(get_current_user_dependency)):
    """Получить настройки приложения"""
    return app_settings

@app.put("/settings", response_model=SettingsResponse)
async def update_settings(settings: SettingsResponse, current_user: dict = Depends(get_current_user_dependency)):
    """Обновить настройки приложения"""
    # Check admin permissions
    if 'admin' not in current_user.get('permissions', []):
        raise HTTPException(
            status_code=403,
            detail="Only admin users can modify settings"
        )
    
    global app_settings
    app_settings = settings.dict()
    return app_settings

# Dashboard stats endpoint
@app.get("/stats", response_model=StatsResponse)
async def get_dashboard_stats(current_user: dict = Depends(get_current_user_dependency)):
    """Получить статистику для панели управления"""
    # Calculate real statistics
    total_queries = len(query_history)
    
    # Get unique users count from query history
    unique_users = set()
    total_execution_time = 0
    successful_queries = 0
    
    for query in query_history:
        if query.get("user"):
            unique_users.add(query["user"])
        
        # Calculate average response time from successful queries
        if query.get("status") == "success" and query.get("execution_time"):
            try:
                exec_time = float(query["execution_time"].replace("s", ""))
                total_execution_time += exec_time
                successful_queries += 1
            except (ValueError, AttributeError):
                pass
    
    # Calculate average response time
    if successful_queries > 0:
        avg_time = total_execution_time / successful_queries
        avg_response_time = f"{avg_time:.2f}s"
    else:
        avg_response_time = "0.00s"
    
    # Get active databases count
    try:
        databases = get_databases()
        active_databases = len(databases)
    except:
        active_databases = 1  # Default fallback
    
    return StatsResponse(
        total_queries=total_queries,
        active_databases=active_databases,
        total_users=len(unique_users),
        avg_response_time=avg_response_time
    )

@app.get("/test/stratification-deps")
async def test_stratification_dependencies():
    """Тестирование зависимостей стратификации"""
    try:
        dependencies_status = {}
        
        # Test pandas
        try:
            import pandas as pd
            dependencies_status["pandas"] = {
                "status": "✅ OK",
                "version": pd.__version__
            }
        except ImportError as e:
            dependencies_status["pandas"] = {
                "status": "❌ ERROR",
                "error": str(e)
            }
        
        # Test numpy
        try:
            import numpy as np
            dependencies_status["numpy"] = {
                "status": "✅ OK", 
                "version": np.__version__
            }
        except ImportError as e:
            dependencies_status["numpy"] = {
                "status": "❌ ERROR",
                "error": str(e)
            }
        
        # Test scikit-learn
        try:
            import sklearn
            from sklearn.model_selection import StratifiedKFold
            dependencies_status["scikit-learn"] = {
                "status": "✅ OK",
                "version": sklearn.__version__
            }
        except ImportError as e:
            dependencies_status["scikit-learn"] = {
                "status": "❌ ERROR",
                "error": str(e)
            }
        
        # Test scipy
        try:
            import scipy
            from scipy.stats import ks_2samp
            dependencies_status["scipy"] = {
                "status": "✅ OK",
                "version": scipy.__version__
            }
        except ImportError as e:
            dependencies_status["scipy"] = {
                "status": "❌ ERROR",
                "error": str(e)
            }
        
        # Test stratification module
        try:
            from stratification import stratify_data
            dependencies_status["stratification_module"] = {
                "status": "✅ OK",
                "note": "Local stratification module imported successfully"
            }
        except ImportError as e:
            dependencies_status["stratification_module"] = {
                "status": "❌ ERROR",
                "error": str(e)
            }
        
        # Overall status
        all_ok = all(dep["status"].startswith("✅") for dep in dependencies_status.values())
        
        return {
            "overall_status": "✅ All dependencies OK" if all_ok else "❌ Some dependencies missing",
            "dependencies": dependencies_status,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "overall_status": "❌ Test failed",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("APP_HOST", "0.0.0.0")
    port = int(os.getenv("APP_PORT", 8000))
    
    uvicorn.run(
        "main:app", 
        host=host, 
        port=port, 
        reload=True,
        log_level="info"
    ) 