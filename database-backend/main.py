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
from scheduler import (
    start_daily_scheduler, stop_daily_scheduler, 
    get_daily_scheduler_status, test_daily_distribution
)

# Load environment variables
load_dotenv()

# Initialize FastAPI app
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("🚀 Starting SoftCollection API server...")
    try:
        # Start the daily distribution scheduler
        await start_daily_scheduler()
        print("✅ Daily distribution scheduler started successfully")
    except Exception as e:
        print(f"⚠️ Warning: Failed to start daily scheduler: {e}")
    
    yield
    
    # Shutdown
    print("🛑 Shutting down SoftCollection API server...")
    try:
        await stop_daily_scheduler()
        print("✅ Daily distribution scheduler stopped successfully")
    except Exception as e:
        print(f"⚠️ Warning: Failed to stop daily scheduler: {e}")
    print("👋 Goodbye!")

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
        # Use case-insensitive lookup for table names
        from database import get_table_columns_case_insensitive
        columns = get_table_columns_case_insensitive(database_id, table_name)
        return columns
    except Exception as e:
        print(f"ERROR in list_columns: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ошибка получения столбцов: {str(e)}")

@app.post("/databases/test-connection", response_model=ConnectionTestResponse)
async def test_db_connection(request: Optional[ConnectionTestRequest] = None, current_user: dict = Depends(get_current_user_dependency)):
    """Тестирование подключения к базе данных DSSB_APP"""
    try:
        result = test_connection()
        return result
    except Exception as e:
        return {
            "status": "error",
            "message": f"Ошибка тестирования соединения DSSB_APP: {str(e)}",
            "connected": False
        }

@app.post("/databases/test-all-connections")
async def test_all_db_connections(current_user: dict = Depends(get_current_user_dependency)):
    """Тестирование подключения к обеим базам данных (DSSB_APP и SPSS)"""
    try:
        from database import test_all_connections
        result = test_all_connections()
        return result
    except Exception as e:
        return {
            "overall_status": "error",
            "message": f"Ошибка тестирования соединений: {str(e)}",
            "dssb_app": {"status": "error", "connected": False, "message": str(e)},
            "spss": {"status": "error", "connected": False, "message": str(e)}
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
        
        # Handle different possible data structures from frontend
        results_data = data.get("results", {})
        
        # Debug logging to help identify issues
        print(f"DEBUG: Received data keys: {list(data.keys())}")
        print(f"DEBUG: Results data type: {type(results_data)}")
        if isinstance(results_data, dict):
            print(f"DEBUG: Results data keys: {list(results_data.keys())}")
        
        # If results is the direct query response structure, extract the data array
        if isinstance(results_data, dict) and "data" in results_data:
            query_results = results_data.get("data", [])
            print(f"DEBUG: Using results.data, found {len(query_results)} rows")
        # If results is already the data array
        elif isinstance(results_data, list):
            query_results = results_data
            print(f"DEBUG: Using results as data array, found {len(query_results)} rows")
        # If results is directly passed in the top level
        elif "data" in data:
            query_results = data.get("data", [])
            print(f"DEBUG: Using data.data, found {len(query_results)} rows")
        else:
            query_results = []
            print("DEBUG: No valid data structure found, using empty array")
        
        if not query_results or len(query_results) == 0:
            print("DEBUG: No query results to analyze")
            return {
                "has_iin_column": False,
                "iin_column": None,
                "iin_values": [],
                "user_count": 0
            }
        
        # Check first row structure for debugging
        if query_results and len(query_results) > 0:
            first_row = query_results[0]
            print(f"DEBUG: First row keys: {list(first_row.keys()) if isinstance(first_row, dict) else 'Not a dict'}")
        
        iin_column = detect_iin_columns(query_results)
        print(f"DEBUG: Detected IIN column: {iin_column}")
        
        if iin_column:
            iin_values = extract_iin_values(query_results, iin_column)
            print(f"DEBUG: Extracted {len(iin_values)} unique IIN values")
            return {
                "has_iin_column": True,
                "iin_column": iin_column,
                "iin_values": iin_values,
                "user_count": len(iin_values)
            }
        else:
            print("DEBUG: No IIN column detected")
            return {
                "has_iin_column": False,
                "iin_column": None,
                "iin_values": [],
                "user_count": 0
            }
            
    except Exception as e:
        print(f"ERROR in detect_iins_in_results: {str(e)}")
        import traceback
        traceback.print_exc()
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
        
        # Validate number of groups (minimum 3, maximum 5)
        num_groups = stratification_config.get("numGroups", 2)
        if num_groups < 3:
            raise HTTPException(status_code=400, detail="Минимальное количество групп для стратификации: 3")
        if num_groups > 5:
            raise HTTPException(status_code=400, detail="Максимальное количество групп для стратификации: 5")

        # Create theories for each stratified group AND insert into SC local tables
        try:
            from database import (create_theory_with_custom_id, get_next_sc_campaign_id, 
                                insert_control_group, insert_target_groups)
        except ImportError as e:
            raise HTTPException(status_code=500, detail=f"Ошибка импорта функций создания теории: {str(e)}")
        
        # Get base campaign ID for this stratification (SC00000001, SC00000002, etc.)
        base_campaign_id = get_next_sc_campaign_id()
        
        created_theories = []
        control_group_inserted = False
        
        # Helper function to get group-specific field from the new frontend structure
        def get_group_field(group_index, field_name):
            """Get field value for specific group from groupFields structure"""
            group_fields = stratification_config.get('groupFields', {})
            group_data = group_fields.get(str(group_index + 1), {})  # Frontend uses 1-based indexing
            return group_data.get(field_name, None) or None
        
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
            theory_name = f"{stratification_config.get('theoryBaseName', 'Стратифицированная кампания')} - Группа {group_letter}"
            theory_description = f"{stratification_config.get('theoryDescription', 'Кампания создана через стратификацию данных')} (Группа {group_letter} - {group.get('num_rows', 0)} записей, пропорция: {group.get('proportion', 0):.3f})"
            theory_start_date = stratification_config.get("theoryStartDate")
            theory_end_date = stratification_config.get("theoryEndDate")
            created_by = current_user["username"]
            
            # Create sub-ID for this group (e.g., SC00000001.1, SC00000001.2, SC00000001.3)
            sub_theory_id = f"{base_campaign_id}.{i + 1}"
            
            # Prepare group-specific additional fields for SC local tables
            additional_fields = {
                'tab1': get_group_field(i, 'tab1') or theory_description,  # Use group-specific tab1 or fall back to description
                'tab2': get_group_field(i, 'tab2'),
                'tab3': get_group_field(i, 'tab3'),
                'tab4': get_group_field(i, 'tab4'),
                'tab5': None  # Keep tab5 as None for now, can be used for future expansion
            }
            
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
                    # Explicit group assignment: First group (Group A) = control, rest = target
                    if i == 0:
                        # Group A: Insert into SC_local_control ONLY (no SPSS)
                        print(f"Processing Group A (control): {group_letter} with {len(iin_values)} users")
                        control_result = insert_control_group(
                            sub_theory_id,
                            iin_values,
                            theory_start_date,
                            theory_end_date,
                            additional_fields
                        )
                        control_group_inserted = True
                        print(f"Control group result: {control_result}")
                    else:
                        # Groups B, C, D, E: Insert into SC_local_target + SPSS.SC_theory_users
                        print(f"Processing Group {group_letter} (target): {group_letter} with {len(iin_values)} users -> DSSB_APP + SPSS")
                        target_result = insert_target_groups(
                            sub_theory_id,  # Use the specific sub-ID, not base campaign ID
                            iin_values,
                            theory_start_date,
                            theory_end_date,
                            additional_fields
                        )
                        print(f"Target group {group_letter} result: {target_result}")
                    
                    created_theories.append({
                        "theory_id": theory_result.get("theory_id"),
                        "theory_name": theory_name,
                        "users_added": theory_result.get("users_added", 0),
                        "group": group_letter,
                        "group_type": "control" if i == 0 else "target",
                        "proportion": group.get("proportion", 0),
                        "num_rows": group.get("num_rows", 0),
                        "sub_id": sub_theory_id
                    })
                else:
                    continue
                    
            except Exception as e:
                print(f"Error creating theory for group {group_letter}: {e}")
                # Continue with other groups even if one fails
                continue
        
        if not created_theories:
            raise HTTPException(status_code=500, detail="Не удалось создать ни одной теории")
        
        execution_time = time.time() - start_time
        
        # Prepare response
        response_data = {
            "success": True,
            "message": f"Успешно создано {len(created_theories)} теорий через стратификацию с базовым Campaign ID {base_campaign_id}",
            "stratification": stratification_result,
            "theories": created_theories,
            "execution_time": f"{execution_time:.3f}s",
            "total_users": sum(theory["users_added"] for theory in created_theories),
            "base_campaign_id": base_campaign_id
        }
        
        # Send success email notification
        try:
            from email_sender import send_campaign_success_notification
            email_sent = send_campaign_success_notification(response_data, current_user["username"])
            if email_sent:
                print(f"Success notification email sent for campaign {base_campaign_id}")
            else:
                print(f"Failed to send success notification email for campaign {base_campaign_id}")
        except Exception as e:
            print(f"Error sending success notification email: {str(e)}")
            # Don't fail the entire operation if email fails
        
        return response_data
        
    except HTTPException as he:
        # Send error email notification for HTTP exceptions
        try:
            from email_sender import send_campaign_error_notification
            error_details = {
                "error": he.detail,
                "operation": "Campaign Stratification",
                "status_code": he.status_code
            }
            send_campaign_error_notification(error_details, current_user["username"])
        except Exception as email_error:
            print(f"Error sending failure notification email: {str(email_error)}")
        
        # Re-raise HTTP exceptions as-is
        raise he
    except Exception as e:
        # Send error email notification for unexpected errors
        try:
            from email_sender import send_campaign_error_notification
            error_details = {
                "error": f"Неожиданная ошибка стратификации: {str(e)}",
                "operation": "Campaign Stratification"
            }
            send_campaign_error_notification(error_details, current_user["username"])
        except Exception as email_error:
            print(f"Error sending failure notification email: {str(email_error)}")
        
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
async def get_data_stats(table_name: str, database_id: str = Query("DSSB_APP"), current_user: dict = Depends(get_current_user_dependency)):
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

# SC Local Tables Data Endpoints
@app.get("/sc-local/control")
async def get_control_group_data(
    theory_id: Optional[str] = Query(None, description="Filter by theory ID"),
    current_user: dict = Depends(get_current_user_dependency)
):
    """Получить данные контрольной группы из SC_local_control"""
    try:
        from database import get_sc_local_data
        
        result = get_sc_local_data("SC_local_control", theory_id)
        
        if result["success"]:
            return {
                "success": True,
                "data": result["data"],
                "total_count": len(result["data"]),
                "message": result["message"]
            }
        else:
            raise HTTPException(status_code=500, detail=result["message"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения данных контрольной группы: {str(e)}")

@app.get("/sc-local/target")
async def get_target_groups_data(
    theory_id: Optional[str] = Query(None, description="Filter by theory ID"),
    current_user: dict = Depends(get_current_user_dependency)
):
    """Получить данные целевых групп из SC_local_target"""
    try:
        from database import get_sc_local_data
        
        result = get_sc_local_data("SC_local_target", theory_id)
        
        if result["success"]:
            return {
                "success": True,
                "data": result["data"],
                "total_count": len(result["data"]),
                "message": result["message"]
            }
        else:
            raise HTTPException(status_code=500, detail=result["message"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения данных целевых групп: {str(e)}")

@app.get("/sc-local/summary/{theory_id}")
async def get_campaign_summary(
    theory_id: str,
    current_user: dict = Depends(get_current_user_dependency)
):
    """Получить сводку по кампании (контроль + целевые группы)"""
    try:
        from database import get_sc_local_data
        
        # Get control group data
        control_result = get_sc_local_data("SC_local_control", theory_id)
        # Get target groups data  
        target_result = get_sc_local_data("SC_local_target", theory_id)
        
        control_count = len(control_result["data"]) if control_result["success"] else 0
        target_count = len(target_result["data"]) if target_result["success"] else 0
        
        return {
            "success": True,
            "theory_id": theory_id,
            "control_group": {
                "count": control_count,
                "data": control_result["data"] if control_result["success"] else []
            },
            "target_groups": {
                "count": target_count,
                "data": target_result["data"] if target_result["success"] else []
            },
            "total_users": control_count + target_count,
            "message": f"Сводка по кампании {theory_id}: {control_count} контроль + {target_count} целевых = {control_count + target_count} всего"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения сводки кампании: {str(e)}")

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

@app.post("/test/email-notifications")
async def test_email_notifications(current_user: dict = Depends(get_current_user_dependency)):
    """Тестирование email уведомлений"""
    try:
        from email_sender import validate_email_config, test_email_notification
        
        # Check email configuration
        if not validate_email_config():
            return {
                "status": "❌ ERROR",
                "message": "Email configuration is invalid",
                "timestamp": datetime.now().isoformat()
            }
        
        # Send test email
        test_result = test_email_notification()
        
        if test_result:
            return {
                "status": "✅ SUCCESS",
                "message": "Test email notification sent successfully",
                "test_user": current_user["username"],
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "status": "❌ ERROR", 
                "message": "Failed to send test email notification",
                "timestamp": datetime.now().isoformat()
            }
            
    except Exception as e:
        return {
            "status": "❌ ERROR",
            "message": f"Error testing email notifications: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }

@app.get("/test/email-config")
async def get_email_config(current_user: dict = Depends(get_current_user_dependency)):
    """Получить информацию о конфигурации email"""
    try:
        from email_sender import (EMAIL_SENDER, SMTP_SERVER, SMTP_PORT, 
                                SMTP_USERNAME, CAMPAIGN_NOTIFICATION_EMAILS)
        
        return {
            "email_sender": EMAIL_SENDER,
            "smtp_server": SMTP_SERVER,
            "smtp_port": SMTP_PORT,
            "smtp_username": SMTP_USERNAME,
            "smtp_password_configured": bool(os.getenv('SMTP_PASSWORD') or True),  # Always True for hardcoded
            "notification_recipients": CAMPAIGN_NOTIFICATION_EMAILS,
            "recipients_count": len(CAMPAIGN_NOTIFICATION_EMAILS),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "error": f"Error getting email configuration: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }

@app.get("/debug/campaign-data-distribution/{base_campaign_id}")
async def get_campaign_data_distribution(
    base_campaign_id: str,
    current_user: dict = Depends(get_current_user_dependency)
):
    """Отладка: показать распределение данных кампании по базам данных"""
    try:
        from database import execute_query, get_connection_SPSS
        
        # Get data from DSSB_APP tables
        control_query = f"""
        SELECT THEORY_ID, COUNT(*) as user_count, 'DSSB_APP.SC_local_control' as source_table
        FROM SC_local_control 
        WHERE THEORY_ID LIKE '{base_campaign_id}%'
        GROUP BY THEORY_ID
        ORDER BY THEORY_ID
        """
        
        target_query = f"""
        SELECT THEORY_ID, COUNT(*) as user_count, 'DSSB_APP.SC_local_target' as source_table
        FROM SC_local_target 
        WHERE THEORY_ID LIKE '{base_campaign_id}%'
        GROUP BY THEORY_ID
        ORDER BY THEORY_ID
        """
        
        control_result = execute_query(control_query)
        target_result = execute_query(target_query)
        
        # Get data from SPSS table
        spss_data = []
        try:
            spss_conn = get_connection_SPSS()
            spss_cursor = spss_conn.cursor()
            
            spss_query = f"""
            SELECT THEORY_ID, COUNT(*) as user_count, 'SPSS.SC_theory_users' as source_table
            FROM SC_theory_users 
            WHERE THEORY_ID LIKE '{base_campaign_id}%'
            GROUP BY THEORY_ID
            ORDER BY THEORY_ID
            """
            
            spss_cursor.execute(spss_query)
            columns = [desc[0].lower() for desc in spss_cursor.description]
            
            for row in spss_cursor.fetchall():
                spss_data.append(dict(zip(columns, row)))
            
            spss_cursor.close()
            spss_conn.close()
            
        except Exception as spss_error:
            spss_data = [{"error": f"SPSS connection failed: {str(spss_error)}"}]
        
        # Compile results
        all_data = []
        
        if control_result["success"]:
            all_data.extend(control_result["data"])
        
        if target_result["success"]:
            all_data.extend(target_result["data"])
        
        all_data.extend(spss_data)
        
        # Create summary
        summary = {
            "control_groups": [item for item in all_data if 'control' in item.get('source_table', '')],
            "target_groups_dssb": [item for item in all_data if 'target' in item.get('source_table', '')],
            "target_groups_spss": [item for item in all_data if 'spss' in item.get('source_table', '').lower()],
            "total_users_control": sum(item.get('user_count', 0) for item in all_data if 'control' in item.get('source_table', '')),
            "total_users_target_dssb": sum(item.get('user_count', 0) for item in all_data if 'target' in item.get('source_table', '')),
            "total_users_spss": sum(item.get('user_count', 0) for item in all_data if 'spss' in item.get('source_table', '').lower()),
        }
        
        return {
            "base_campaign_id": base_campaign_id,
            "data_distribution": all_data,
            "summary": summary,
            "expected_behavior": {
                "control_groups": "Should only appear in DSSB_APP.SC_local_control",
                "target_groups": "Should appear in both DSSB_APP.SC_local_target AND SPSS.SC_theory_users",
                "spss_should_not_contain": "Control groups (ending in .1)"
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
                 return {
             "error": f"Error getting campaign data distribution: {str(e)}",
             "timestamp": datetime.now().isoformat()
         }

@app.post("/debug/cleanup-spss-control-groups")
async def cleanup_spss_control_groups(current_user: dict = Depends(get_current_user_dependency)):
    """Отладка: удалить контрольные группы из SPSS.SC_theory_users (они должны быть только в control)"""
    try:
        from database import get_connection_SPSS
        
        # Check admin permissions for this dangerous operation
        if 'admin' not in current_user.get('permissions', []):
            return {
                "error": "Only admin users can perform SPSS cleanup operations",
                "timestamp": datetime.now().isoformat()
            }
        
        cleanup_results = {
            "found_control_groups": [],
            "deleted_records": 0,
            "errors": []
        }
        
        try:
            spss_conn = get_connection_SPSS()
            spss_cursor = spss_conn.cursor()
            
            # First, find control groups in SPSS (they end with .1)
            find_query = r"""
            SELECT THEORY_ID, COUNT(*) as user_count
            FROM SC_theory_users 
            WHERE REGEXP_LIKE(THEORY_ID, '^SC[0-9]{8}\.1$')
            GROUP BY THEORY_ID
            ORDER BY THEORY_ID
            """
            
            spss_cursor.execute(find_query)
            for row in spss_cursor.fetchall():
                theory_id, user_count = row
                cleanup_results["found_control_groups"].append({
                    "theory_id": theory_id,
                    "user_count": user_count
                })
            
            # If control groups found, delete them
            if cleanup_results["found_control_groups"]:
                delete_query = r"""
                DELETE FROM SC_theory_users 
                WHERE REGEXP_LIKE(THEORY_ID, '^SC[0-9]{8}\.1$')
                """
                
                spss_cursor.execute(delete_query)
                cleanup_results["deleted_records"] = spss_cursor.rowcount
                spss_conn.commit()
                
                print(f"Cleaned up {cleanup_results['deleted_records']} control group records from SPSS")
            
            spss_cursor.close()
            spss_conn.close()
            
            return {
                "success": True,
                "message": f"Cleanup completed. Removed {cleanup_results['deleted_records']} control group records from SPSS.",
                "details": cleanup_results,
                "note": "Control groups should only exist in DSSB_APP.SC_local_control, not in SPSS.SC_theory_users",
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as spss_error:
            return {
                "success": False,
                "error": f"SPSS cleanup failed: {str(spss_error)}",
                "timestamp": datetime.now().isoformat()
            }
        
    except Exception as e:
        return {
            "error": f"Error during SPSS cleanup: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }

# Daily Distribution Scheduler Management Endpoints
@app.get("/scheduler/status")
async def get_scheduler_status(current_user: dict = Depends(get_current_user_dependency)):
    """Получить статус планировщика ежедневной дистрибуции"""
    try:
        status = get_daily_scheduler_status()
        return {
            "success": True,
            "scheduler_status": status,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Error getting scheduler status: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }

@app.post("/scheduler/test-distribution")
async def test_distribution_manually(current_user: dict = Depends(get_current_user_dependency)):
    """Запустить тестовый запуск ежедневной дистрибуции"""
    try:
        # Check admin permissions for manual distribution
        if 'admin' not in current_user.get('permissions', []):
            return {
                "success": False,
                "error": "Only admin users can run manual distribution tests",
                "timestamp": datetime.now().isoformat()
            }
        
        result = await test_daily_distribution()
        
        return {
            "success": True,
            "test_result": result,
            "message": "Manual distribution test completed",
            "run_by": current_user["username"],
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Error running manual distribution test: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }

@app.get("/scheduler/next-runs")
async def get_next_scheduled_runs(current_user: dict = Depends(get_current_user_dependency)):
    """Получить информацию о следующих запланированных запусках"""
    try:
        status = get_daily_scheduler_status()
        
        next_runs = []
        if status.get("status") == "running" and status.get("jobs"):
            for job in status["jobs"]:
                if job.get("next_run"):
                    next_runs.append({
                        "job_name": job["name"],
                        "job_id": job["id"],
                        "next_run": job["next_run"],
                        "trigger": job["trigger"]
                    })
        
        return {
            "success": True,
            "scheduler_running": status.get("status") == "running",
            "timezone": status.get("timezone", "Asia/Almaty"),
            "next_runs": next_runs,
            "total_scheduled_jobs": len(next_runs),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Error getting scheduled runs: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }

@app.get("/daily-distribution/preview")
async def preview_daily_distribution(current_user: dict = Depends(get_current_user_dependency)):
    """Предварительный просмотр данных для ежедневной дистрибуции без выполнения"""
    try:
        from database import (
            get_active_campaigns_for_daily_process,
            get_spss_count_day_5_users,
            distribute_users_to_campaigns
        )
        
        # Step 1: Get active campaigns
        campaigns_result = get_active_campaigns_for_daily_process()
        if not campaigns_result["success"]:
            return {
                "success": False,
                "error": f"Failed to get active campaigns: {campaigns_result['message']}",
                "timestamp": datetime.now().isoformat()
            }
        
        # Step 2: Get SPSS users
        spss_users_result = get_spss_count_day_5_users()
        if not spss_users_result["success"]:
            return {
                "success": False,
                "error": f"Failed to get SPSS users: {spss_users_result['message']}",
                "timestamp": datetime.now().isoformat()
            }
        
        # Step 3: Create distribution plan (without executing)
        distribution_plan = None
        if campaigns_result["campaigns"] and spss_users_result["iin_values"]:
            distribution_result = distribute_users_to_campaigns(
                spss_users_result["iin_values"],
                campaigns_result["campaigns"]
            )
            if distribution_result["success"]:
                distribution_plan = distribution_result["distributions"]
        
        return {
            "success": True,
            "preview": {
                "active_campaigns": campaigns_result["campaigns"],
                "campaigns_count": campaigns_result["count"],
                "available_users": spss_users_result["count"],
                "users_sample": spss_users_result["iin_values"][:5] if spss_users_result["iin_values"] else [],  # Show first 5 as sample
                "distribution_plan": distribution_plan,
                "would_distribute": distribution_result["total_users_distributed"] if distribution_plan else 0
            },
            "timestamp": datetime.now().isoformat(),
            "note": "This is a preview only - no data was actually distributed"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Error creating distribution preview: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }

@app.get("/monitoring/overview")
async def get_monitoring_overview(current_user: dict = Depends(get_current_user_dependency)):
    """Get high-level monitoring overview of all tables and activities"""
    try:
        from database import execute_query, get_connection_SPSS
        
        overview = {
            "timestamp": datetime.now().isoformat(),
            "tables": {},
            "campaigns": {},
            "daily_activity": {},
            "recent_uploads": []
        }
        
        # Get SC_local_control statistics
        control_stats_query = """
        SELECT 
            COUNT(*) as total_users,
            COUNT(DISTINCT THEORY_ID) as unique_campaigns,
            MIN(insert_datetime) as earliest_upload,
            MAX(insert_datetime) as latest_upload
        FROM SC_local_control
        """
        control_result = execute_query(control_stats_query)
        if control_result["success"] and control_result["data"]:
            overview["tables"]["sc_local_control"] = control_result["data"][0]
        
        # Get SC_local_target statistics
        target_stats_query = """
        SELECT 
            COUNT(*) as total_users,
            COUNT(DISTINCT THEORY_ID) as unique_campaigns,
            MIN(insert_datetime) as earliest_upload,
            MAX(insert_datetime) as latest_upload
        FROM SC_local_target
        """
        target_result = execute_query(target_stats_query)
        if target_result["success"] and target_result["data"]:
            overview["tables"]["sc_local_target"] = target_result["data"][0]
        
        # Get SPSS statistics
        try:
            spss_conn = get_connection_SPSS()
            spss_cursor = spss_conn.cursor()
            
            spss_stats_query = """
            SELECT 
                COUNT(*) as total_users,
                COUNT(DISTINCT THEORY_ID) as unique_campaigns,
                MIN(insert_datetime) as earliest_upload,
                MAX(insert_datetime) as latest_upload
            FROM SC_theory_users
            """
            spss_cursor.execute(spss_stats_query)
            columns = [desc[0].lower() for desc in spss_cursor.description]
            row = spss_cursor.fetchone()
            if row:
                overview["tables"]["spss_sc_theory_users"] = dict(zip(columns, row))
            
            spss_cursor.close()
            spss_conn.close()
            
        except Exception as spss_error:
            overview["tables"]["spss_sc_theory_users"] = {"error": str(spss_error)}
        
        # Get campaign registry statistics
        campaign_stats_query = """
        SELECT 
            COUNT(*) as total_campaigns,
            COUNT(CASE WHEN SYSDATE BETWEEN theory_start_date AND theory_end_date THEN 1 END) as active_campaigns,
            SUM(user_count) as total_planned_users,
            MIN(load_date) as earliest_campaign,
            MAX(load_date) as latest_campaign
        FROM SoftCollection_theories
        """
        campaign_result = execute_query(campaign_stats_query)
        if campaign_result["success"] and campaign_result["data"]:
            overview["campaigns"] = campaign_result["data"][0]
        
        return {
            "success": True,
            "overview": overview
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Error getting monitoring overview: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }

@app.get("/monitoring/daily-statistics")
async def get_daily_statistics(
    days_back: int = Query(7, ge=1, le=30, description="Number of days to look back"),
    current_user: dict = Depends(get_current_user_dependency)
):
    """Get daily upload statistics for the last N days"""
    try:
        from database import execute_query, get_connection_SPSS
        
        daily_stats = {
            "period": f"Last {days_back} days",
            "timestamp": datetime.now().isoformat(),
            "sc_local_control": [],
            "sc_local_target": [],
            "spss_sc_theory_users": [],
            "summary": {}
        }
        
        # SC_local_control daily statistics
        control_daily_query = f"""
        SELECT 
            TO_CHAR(insert_datetime, 'YYYY-MM-DD') as upload_date,
            COUNT(*) as users_uploaded,
            COUNT(DISTINCT THEORY_ID) as campaigns_affected,
            COUNT(DISTINCT IIN) as unique_users
        FROM SC_local_control
        WHERE insert_datetime >= SYSDATE - {days_back}
        GROUP BY TO_CHAR(insert_datetime, 'YYYY-MM-DD')
        ORDER BY upload_date DESC
        """
        control_result = execute_query(control_daily_query)
        if control_result["success"]:
            daily_stats["sc_local_control"] = control_result["data"]
        
        # SC_local_target daily statistics
        target_daily_query = f"""
        SELECT 
            TO_CHAR(insert_datetime, 'YYYY-MM-DD') as upload_date,
            COUNT(*) as users_uploaded,
            COUNT(DISTINCT THEORY_ID) as campaigns_affected,
            COUNT(DISTINCT IIN) as unique_users
        FROM SC_local_target
        WHERE insert_datetime >= SYSDATE - {days_back}
        GROUP BY TO_CHAR(insert_datetime, 'YYYY-MM-DD')
        ORDER BY upload_date DESC
        """
        target_result = execute_query(target_daily_query)
        if target_result["success"]:
            daily_stats["sc_local_target"] = target_result["data"]
        
        # SPSS daily statistics
        try:
            spss_conn = get_connection_SPSS()
            spss_cursor = spss_conn.cursor()
            
            spss_daily_query = f"""
            SELECT 
                TO_CHAR(insert_datetime, 'YYYY-MM-DD') as upload_date,
                COUNT(*) as users_uploaded,
                COUNT(DISTINCT THEORY_ID) as campaigns_affected,
                COUNT(DISTINCT IIN) as unique_users
            FROM SC_theory_users
            WHERE insert_datetime >= SYSDATE - {days_back}
            GROUP BY TO_CHAR(insert_datetime, 'YYYY-MM-DD')
            ORDER BY upload_date DESC
            """
            spss_cursor.execute(spss_daily_query)
            columns = [desc[0].lower() for desc in spss_cursor.description]
            
            spss_daily_data = []
            for row in spss_cursor.fetchall():
                spss_daily_data.append(dict(zip(columns, row)))
            daily_stats["spss_sc_theory_users"] = spss_daily_data
            
            spss_cursor.close()
            spss_conn.close()
            
        except Exception as spss_error:
            daily_stats["spss_sc_theory_users"] = [{"error": str(spss_error)}]
        
        # Calculate summary statistics
        total_control = sum(day.get("users_uploaded", 0) for day in daily_stats["sc_local_control"])
        total_target = sum(day.get("users_uploaded", 0) for day in daily_stats["sc_local_target"])
        total_spss = sum(day.get("users_uploaded", 0) for day in daily_stats["spss_sc_theory_users"] if "error" not in day)
        
        daily_stats["summary"] = {
            "total_control_uploads": total_control,
            "total_target_uploads": total_target,
            "total_spss_uploads": total_spss,
            "total_uploads": total_control + total_target + total_spss
        }
        
        return {
            "success": True,
            "daily_statistics": daily_stats
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Error getting daily statistics: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }

@app.get("/monitoring/campaign-distribution")
async def get_campaign_distribution(current_user: dict = Depends(get_current_user_dependency)):
    """Get user distribution by campaigns across all tables"""
    try:
        from database import execute_query, get_connection_SPSS
        
        distribution = {
            "timestamp": datetime.now().isoformat(),
            "campaigns": [],
            "totals": {}
        }
        
        # Get campaign distribution from all tables
        campaign_dist_query = r"""
        WITH campaign_summary AS (
            SELECT 
                st.theory_id,
                st.theory_name,
                TO_CHAR(st.theory_start_date, 'YYYY-MM-DD') as theory_start_date,
                TO_CHAR(st.theory_end_date, 'YYYY-MM-DD') as theory_end_date,
                st.user_count as planned_users,
                CASE WHEN SYSDATE BETWEEN st.theory_start_date AND st.theory_end_date THEN 'Active' ELSE 'Inactive' END as status
            FROM SoftCollection_theories st
        ),
        control_counts AS (
            SELECT 
                CASE 
                    WHEN REGEXP_LIKE(theory_id, '^SC[0-9]{8}\.[0-9]+$') THEN
                        SUBSTR(theory_id, 1, INSTR(theory_id, '.') - 1)
                    ELSE theory_id
                END as base_campaign_id,
                COUNT(*) as control_users
            FROM SC_local_control
            GROUP BY CASE 
                WHEN REGEXP_LIKE(theory_id, '^SC[0-9]{8}\.[0-9]+$') THEN
                    SUBSTR(theory_id, 1, INSTR(theory_id, '.') - 1)
                ELSE theory_id
            END
        ),
        target_counts AS (
            SELECT 
                CASE 
                    WHEN REGEXP_LIKE(theory_id, '^SC[0-9]{8}\.[0-9]+$') THEN
                        SUBSTR(theory_id, 1, INSTR(theory_id, '.') - 1)
                    ELSE theory_id
                END as base_campaign_id,
                COUNT(*) as target_users
            FROM SC_local_target
            GROUP BY CASE 
                WHEN REGEXP_LIKE(theory_id, '^SC[0-9]{8}\.[0-9]+$') THEN
                    SUBSTR(theory_id, 1, INSTR(theory_id, '.') - 1)
                ELSE theory_id
            END
        )
        SELECT 
            cs.theory_id,
            cs.theory_name,
            cs.theory_start_date,
            cs.theory_end_date,
            cs.planned_users,
            cs.status,
            NVL(cc.control_users, 0) as control_users,
            NVL(tc.target_users, 0) as target_users,
            (NVL(cc.control_users, 0) + NVL(tc.target_users, 0)) as total_actual_users
        FROM campaign_summary cs
        LEFT JOIN control_counts cc ON (
            CASE 
                WHEN REGEXP_LIKE(cs.theory_id, '^SC[0-9]{8}\.[0-9]+$') THEN
                    SUBSTR(cs.theory_id, 1, INSTR(cs.theory_id, '.') - 1)
                ELSE cs.theory_id
            END = cc.base_campaign_id
        )
        LEFT JOIN target_counts tc ON (
            CASE 
                WHEN REGEXP_LIKE(cs.theory_id, '^SC[0-9]{8}\.[0-9]+$') THEN
                    SUBSTR(cs.theory_id, 1, INSTR(cs.theory_id, '.') - 1)
                ELSE cs.theory_id
            END = tc.base_campaign_id
        )
        ORDER BY cs.theory_start_date DESC, cs.theory_id DESC
        """
        
        campaign_result = execute_query(campaign_dist_query)
        if campaign_result["success"]:
            distribution["campaigns"] = campaign_result["data"]
        
        # Get SPSS counts for each campaign
        try:
            spss_conn = get_connection_SPSS()
            spss_cursor = spss_conn.cursor()
            
            spss_dist_query = r"""
            SELECT 
                CASE 
                    WHEN REGEXP_LIKE(theory_id, '^SC[0-9]{8}\.[0-9]+$') THEN
                        SUBSTR(theory_id, 1, INSTR(theory_id, '.') - 1)
                    ELSE theory_id
                END as base_campaign_id,
                COUNT(*) as spss_users
            FROM SC_theory_users
            GROUP BY CASE 
                WHEN REGEXP_LIKE(theory_id, '^SC[0-9]{8}\.[0-9]+$') THEN
                    SUBSTR(theory_id, 1, INSTR(theory_id, '.') - 1)
                ELSE theory_id
            END
            """
            spss_cursor.execute(spss_dist_query)
            
            spss_counts = {}
            for row in spss_cursor.fetchall():
                base_id, count = row
                spss_counts[base_id] = count
            
            # Add SPSS counts to campaigns
            for campaign in distribution["campaigns"]:
                base_id = campaign["theory_id"]
                if "." in base_id:
                    base_id = base_id.split(".")[0]
                campaign["spss_users"] = spss_counts.get(base_id, 0)
            
            spss_cursor.close()
            spss_conn.close()
            
        except Exception as spss_error:
            for campaign in distribution["campaigns"]:
                campaign["spss_users"] = f"Error: {spss_error}"
        
        # Calculate totals
        distribution["totals"] = {
            "total_campaigns": len(distribution["campaigns"]),
            "active_campaigns": len([c for c in distribution["campaigns"] if c["status"] == "Active"]),
            "total_control_users": sum(c.get("control_users", 0) for c in distribution["campaigns"]),
            "total_target_users": sum(c.get("target_users", 0) for c in distribution["campaigns"]),
            "total_planned_users": sum(c.get("planned_users", 0) for c in distribution["campaigns"]),
            "total_actual_users": sum(c.get("total_actual_users", 0) for c in distribution["campaigns"])
        }
        
        return {
            "success": True,
            "campaign_distribution": distribution
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Error getting campaign distribution: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }

@app.get("/monitoring/recent-activity")
async def get_recent_activity(
    limit: int = Query(50, ge=10, le=200, description="Number of recent records to fetch"),
    current_user: dict = Depends(get_current_user_dependency)
):
    """Get recent upload activity across all tables"""
    try:
        from database import execute_query, get_connection_SPSS
        
        recent_activity = {
            "timestamp": datetime.now().isoformat(),
            "activities": [],
            "summary": {},
            "debug_info": {}
        }
        
        # Simplified query - get most recent uploads without grouping by tab fields
        # This should capture today's data if it was loaded
        control_activity_query = f"""
        SELECT 
            'Control Group' as activity_type,
            THEORY_ID,
            COUNT(*) as users_count,
            TO_CHAR(MAX(insert_datetime), 'YYYY-MM-DD HH24:MI:SS') as upload_time,
            MAX(tab1) as tab1, 
            MAX(tab2) as tab2
        FROM SC_local_control
        WHERE insert_datetime >= SYSDATE - 30
        GROUP BY THEORY_ID
        ORDER BY MAX(insert_datetime) DESC
        FETCH FIRST {limit//2} ROWS ONLY
        """
        control_result = execute_query(control_activity_query)
        if control_result["success"]:
            recent_activity["activities"].extend(control_result["data"])
            recent_activity["debug_info"]["control_count"] = len(control_result["data"])
        else:
            recent_activity["debug_info"]["control_error"] = control_result.get("error", "Unknown error")
        
        # Get recent activities from SC_local_target
        target_activity_query = f"""
        SELECT 
            'Target Group' as activity_type,
            THEORY_ID,
            COUNT(*) as users_count,
            TO_CHAR(MAX(insert_datetime), 'YYYY-MM-DD HH24:MI:SS') as upload_time,
            MAX(tab1) as tab1, 
            MAX(tab2) as tab2
        FROM SC_local_target
        WHERE insert_datetime >= SYSDATE - 30
        GROUP BY THEORY_ID
        ORDER BY MAX(insert_datetime) DESC
        FETCH FIRST {limit//2} ROWS ONLY
        """
        target_result = execute_query(target_activity_query)
        if target_result["success"]:
            recent_activity["activities"].extend(target_result["data"])
            recent_activity["debug_info"]["target_count"] = len(target_result["data"])
        else:
            recent_activity["debug_info"]["target_error"] = target_result.get("error", "Unknown error")
        
        # Get recent activities from SPSS
        try:
            spss_conn = get_connection_SPSS()
            spss_cursor = spss_conn.cursor()
            
            spss_activity_query = f"""
            SELECT 
                'SPSS Target' as activity_type,
                THEORY_ID,
                COUNT(*) as users_count,
                TO_CHAR(MAX(insert_datetime), 'YYYY-MM-DD HH24:MI:SS') as upload_time,
                MAX(tab1) as tab1, 
                MAX(tab2) as tab2
            FROM SC_theory_users
            WHERE insert_datetime >= SYSDATE - 30
            GROUP BY THEORY_ID
            ORDER BY MAX(insert_datetime) DESC
            FETCH FIRST {limit//2} ROWS ONLY
            """
            spss_cursor.execute(spss_activity_query)
            columns = [desc[0].lower() for desc in spss_cursor.description]
            
            spss_data = []
            for row in spss_cursor.fetchall():
                spss_data.append(dict(zip(columns, row)))
            
            recent_activity["activities"].extend(spss_data)
            recent_activity["debug_info"]["spss_count"] = len(spss_data)
            
            spss_cursor.close()
            spss_conn.close()
            
        except Exception as spss_error:
            print(f"SPSS error in recent activity: {spss_error}")
            recent_activity["debug_info"]["spss_error"] = str(spss_error)
        
        # Sort all activities by upload_time
        valid_activities = [a for a in recent_activity["activities"] if "upload_time" in a]
        valid_activities.sort(key=lambda x: x["upload_time"], reverse=True)
        recent_activity["activities"] = valid_activities[:limit]
        
        # Calculate summary
        recent_activity["summary"] = {
            "total_activities": len(valid_activities),
            "unique_campaigns": len(set(a.get("theory_id", "") for a in valid_activities if a.get("theory_id"))),
            "total_users_uploaded": sum(a.get("users_count", 0) for a in valid_activities),
            "period": "Last 30 days"
        }
        
        return {
            "success": True,
            "recent_activity": recent_activity
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Error getting recent activity: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }

@app.get("/debug/recent-activity-raw")
async def debug_recent_activity_raw(current_user: dict = Depends(get_current_user_dependency)):
    """Debug endpoint to check raw recent activity data"""
    try:
        from database import execute_query, get_connection_SPSS
        
        debug_info = {
            "timestamp": datetime.now().isoformat(),
            "local_control": {},
            "local_target": {},
            "spss_theory": {}
        }
        
        # Check SC_local_control raw data
        control_debug_query = """
        SELECT 
            COUNT(*) as total_records,
            COUNT(DISTINCT THEORY_ID) as unique_campaigns,
            TO_CHAR(MIN(insert_datetime), 'YYYY-MM-DD HH24:MI:SS') as earliest_insert,
            TO_CHAR(MAX(insert_datetime), 'YYYY-MM-DD HH24:MI:SS') as latest_insert,
            COUNT(CASE WHEN insert_datetime >= SYSDATE - 1 THEN 1 END) as today_records,
            COUNT(CASE WHEN insert_datetime >= SYSDATE - 7 THEN 1 END) as week_records
        FROM SC_local_control
        """
        control_result = execute_query(control_debug_query)
        if control_result["success"] and control_result["data"]:
            debug_info["local_control"] = control_result["data"][0]
        
        # Check SC_local_target raw data  
        target_debug_query = """
        SELECT 
            COUNT(*) as total_records,
            COUNT(DISTINCT THEORY_ID) as unique_campaigns,
            TO_CHAR(MIN(insert_datetime), 'YYYY-MM-DD HH24:MI:SS') as earliest_insert,
            TO_CHAR(MAX(insert_datetime), 'YYYY-MM-DD HH24:MI:SS') as latest_insert,
            COUNT(CASE WHEN insert_datetime >= SYSDATE - 1 THEN 1 END) as today_records,
            COUNT(CASE WHEN insert_datetime >= SYSDATE - 7 THEN 1 END) as week_records
        FROM SC_local_target
        """
        target_result = execute_query(target_debug_query)
        if target_result["success"] and target_result["data"]:
            debug_info["local_target"] = target_result["data"][0]
        
        # Check SPSS data
        try:
            spss_conn = get_connection_SPSS()
            spss_cursor = spss_conn.cursor()
            
            spss_debug_query = """
            SELECT 
                COUNT(*) as total_records,
                COUNT(DISTINCT THEORY_ID) as unique_campaigns,
                TO_CHAR(MIN(insert_datetime), 'YYYY-MM-DD HH24:MI:SS') as earliest_insert,
                TO_CHAR(MAX(insert_datetime), 'YYYY-MM-DD HH24:MI:SS') as latest_insert,
                COUNT(CASE WHEN insert_datetime >= SYSDATE - 1 THEN 1 END) as today_records,
                COUNT(CASE WHEN insert_datetime >= SYSDATE - 7 THEN 1 END) as week_records
            FROM SC_theory_users
            """
            spss_cursor.execute(spss_debug_query)
            columns = [desc[0].lower() for desc in spss_cursor.description]
            row = spss_cursor.fetchone()
            if row:
                debug_info["spss_theory"] = dict(zip(columns, row))
            
            spss_cursor.close()
            spss_conn.close()
            
        except Exception as spss_error:
            debug_info["spss_theory"] = {"error": str(spss_error)}
        
        return {
            "success": True,
            "debug_info": debug_info
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Error in debug endpoint: {str(e)}",
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