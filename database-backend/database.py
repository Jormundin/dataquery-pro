import os
import cx_Oracle
from typing import List, Dict, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Hardcoded list of tables that frontend has access to
ALLOWED_TABLES = {
    'DSSB_APP': {
        'DSSB_DM.RB_CLIENTS': {
            'description': 'Информация о клиентах',
            'columns': [
                {'name': 'SNAPSHOT_DATE', 'type': 'DATE', 'description': 'DATE'},
                {'name': 'OCRM_DWH_ID', 'type': 'NUMBER', 'description': 'ID'},
                {'name': 'GM_SYSTEM_CODE', 'type': 'VARCHAR2', 'description': 'ID'},
                {'name': 'IIN_BIN', 'type': 'NUMBER', 'description': 'ID'},
                {'name': 'OCRM_ID', 'type': 'VARCHAR2', 'description': 'ID'},
                {'name': 'LAST_NAME', 'type': 'VARCHAR2', 'description': 'NAME'},
                {'name': 'FIRST_NAME', 'type': 'VARCHAR2', 'description': 'NAME'},
                {'name': 'MIDDLE_NAME', 'type': 'VARCHAR2', 'description': 'NAME'},
                {'name': 'LONG_NAME', 'type': 'VARCHAR2', 'description': 'NAME'},
                {'name': 'SEX_CODE', 'type': 'VARCHAR2', 'description': 'Статус'},
                {'name': 'MARITAL_STATUS', 'type': 'VARCHAR2', 'description': 'Статус'},
                {'name': 'BIRTH_DATE', 'type': 'DATE', 'description': 'DATE'},
                {'name': 'CITY_RESIDENCE', 'type': 'VARCHAR2', 'description': 'NAME'},
                {'name': 'AGE', 'type': 'DATE', 'description': 'DATE'},
            ]
    },
        'DSSB_APP.SoftCollection_theories': {
            'description': 'Реестр кампаний Soft Collection (одна запись на кампанию)',
            'columns': [
                {'name': 'THEORY_ID', 'type': 'VARCHAR2', 'description': 'Уникальный ID кампании'},
                {'name': 'THEORY_NAME', 'type': 'VARCHAR2', 'description': 'Название кампании'},
                {'name': 'THEORY_DESCRIPTION', 'type': 'VARCHAR2', 'description': 'Описание кампании'},
                {'name': 'LOAD_DATE', 'type': 'DATE', 'description': 'Дата создания записи'},
                {'name': 'THEORY_START_DATE', 'type': 'DATE', 'description': 'Дата начала кампании'},
                {'name': 'THEORY_END_DATE', 'type': 'DATE', 'description': 'Дата окончания кампании'},
                {'name': 'USER_COUNT', 'type': 'NUMBER', 'description': 'Количество пользователей в кампании'},
                {'name': 'CREATED_BY', 'type': 'VARCHAR2', 'description': 'Кто создал кампанию'},
            ]
        },
        'DSSB_APP.SC_local_control': {
            'description': 'Контрольная группа пользователей из стратификации',
            'columns': [
                {'name': 'IIN', 'type': 'VARCHAR2', 'description': 'Индивидуальный идентификационный номер'},
                {'name': 'THEORY_ID', 'type': 'VARCHAR2', 'description': 'ID кампании'},
                {'name': 'DATE_START', 'type': 'DATE', 'description': 'Дата начала кампании'},
                {'name': 'DATE_END', 'type': 'DATE', 'description': 'Дата окончания кампании'},
                {'name': 'INSERT_DATETIME', 'type': 'DATE', 'description': 'Время вставки записи'},
                {'name': 'TAB1', 'type': 'VARCHAR2', 'description': 'Дополнительное поле 1'},
                {'name': 'TAB2', 'type': 'VARCHAR2', 'description': 'Дополнительное поле 2'},
                {'name': 'TAB3', 'type': 'VARCHAR2', 'description': 'Дополнительное поле 3'},
                {'name': 'TAB4', 'type': 'VARCHAR2', 'description': 'Дополнительное поле 4'},
                {'name': 'TAB5', 'type': 'VARCHAR2', 'description': 'Дополнительное поле 5'},
            ]
        },
        'DSSB_APP.SC_local_target': {
            'description': 'Целевые группы пользователей из стратификации',
            'columns': [
                {'name': 'IIN', 'type': 'VARCHAR2', 'description': 'Индивидуальный идентификационный номер'},
                {'name': 'THEORY_ID', 'type': 'VARCHAR2', 'description': 'ID кампании'},
                {'name': 'DATE_START', 'type': 'DATE', 'description': 'Дата начала кампании'},
                {'name': 'DATE_END', 'type': 'DATE', 'description': 'Дата окончания кампании'},
                {'name': 'INSERT_DATETIME', 'type': 'DATE', 'description': 'Время вставки записи'},
                {'name': 'TAB1', 'type': 'VARCHAR2', 'description': 'Дополнительное поле 1'},
                {'name': 'TAB2', 'type': 'VARCHAR2', 'description': 'Дополнительное поле 2'},
                {'name': 'TAB3', 'type': 'VARCHAR2', 'description': 'Дополнительное поле 3'},
                {'name': 'TAB4', 'type': 'VARCHAR2', 'description': 'Дополнительное поле 4'},
                {'name': 'TAB5', 'type': 'VARCHAR2', 'description': 'Дополнительное поле 5'},
            ]
        }
    }
}

def get_connection_DSSB_APP():
    """Establish a connection to the DSSB_APP database"""
    try:
        # Get database configuration from environment variables
        oracle_host = os.getenv('ORACLE_HOST', '')
        oracle_port = os.getenv('ORACLE_PORT', '1521')
        oracle_sid = os.getenv('ORACLE_SID', '')
        oracle_user = os.getenv('ORACLE_USER', '')
        oracle_password = os.getenv('ORACLE_PASSWORD', '')
        
        if not all([oracle_host, oracle_sid, oracle_user, oracle_password]):
            raise ValueError("Missing required database environment variables. Please check ORACLE_HOST, ORACLE_SID, ORACLE_USER, and ORACLE_PASSWORD.")
        
        dsn = cx_Oracle.makedsn(oracle_host, oracle_port, sid=oracle_sid)
        return cx_Oracle.connect(user=oracle_user, password=oracle_password, dsn=dsn)
    except cx_Oracle.Error as e:
        print(f"Database connection error: {str(e)}")
        raise
    except ValueError as e:
        print(f"Configuration error: {str(e)}")
        raise
    except Exception as e:
        print(f"Unexpected error in database connection: {str(e)}")
        raise

def get_connection_SPSS():
    """Establish a connection to the SPSS database"""
    try:
        # Get SPSS database configuration from environment variables
        spss_host = os.getenv('SPSS_ORACLE_HOST', '')
        spss_port = os.getenv('SPSS_ORACLE_PORT', '1521')
        spss_sid = os.getenv('SPSS_ORACLE_SID', '')
        spss_user = os.getenv('SPSS_ORACLE_USER', '')
        spss_password = os.getenv('SPSS_ORACLE_PASSWORD', '')
        
        if not all([spss_host, spss_sid, spss_user, spss_password]):
            raise ValueError("Missing required SPSS database environment variables. Please check SPSS_ORACLE_HOST, SPSS_ORACLE_SID, SPSS_ORACLE_USER, and SPSS_ORACLE_PASSWORD.")
        
        dsn = cx_Oracle.makedsn(spss_host, spss_port, sid=spss_sid)
        return cx_Oracle.connect(user=spss_user, password=spss_password, dsn=dsn)
    except cx_Oracle.Error as e:
        print(f"SPSS Database connection error: {str(e)}")
        raise
    except ValueError as e:
        print(f"SPSS Configuration error: {str(e)}")
        raise
    except Exception as e:
        print(f"Unexpected error in SPSS database connection: {str(e)}")
        raise

def test_connection() -> Dict:
    """Test database connection and return status"""
    try:
        conn = get_connection_DSSB_APP()
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM DUAL")
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        
        return {
            "status": "success",
            "message": "Соединение с базой данных DSSB_APP установлено успешно",
            "connected": True
        }
    except Exception as e:
        return {
            "status": "error", 
            "message": f"Ошибка подключения к базе данных DSSB_APP: {str(e)}",
            "connected": False
        }

def test_spss_connection() -> Dict:
    """Test SPSS database connection and return status"""
    try:
        conn = get_connection_SPSS()
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM DUAL")
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        
        return {
            "status": "success",
            "message": "Соединение с базой данных SPSS установлено успешно",
            "connected": True
        }
    except Exception as e:
        return {
            "status": "error", 
            "message": f"Ошибка подключения к базе данных SPSS: {str(e)}",
            "connected": False
        }

def test_all_connections() -> Dict:
    """Test both DSSB_APP and SPSS database connections"""
    dssb_result = test_connection()
    spss_result = test_spss_connection()
    
    return {
        "dssb_app": dssb_result,
        "spss": spss_result,
        "overall_status": "success" if dssb_result["connected"] and spss_result["connected"] else "partial" if dssb_result["connected"] or spss_result["connected"] else "error",
        "message": f"DSSB_APP: {dssb_result['status']}, SPSS: {spss_result['status']}"
    }

def get_databases() -> List[Dict]:
    """Get list of available databases"""
    return [
        {
            "id": "dssb_app",
            "name": "Продуктивная база данных DSSB_APP",
            "description": "Основная корпоративная база данных",
            "status": "active"
        }
    ]

def get_tables(database_id: str) -> List[Dict]:
    """Get list of tables for a specific database"""
    if database_id not in ALLOWED_TABLES:
        return []
    
    tables = []
    for table_name, table_info in ALLOWED_TABLES[database_id].items():
        tables.append({
            "name": table_name,
            "description": table_info["description"],
            "columns_count": len(table_info["columns"])
        })
    
    return tables

def get_table_columns(database_id: str, table_name: str) -> List[Dict]:
    """Get columns for a specific table"""
    if database_id not in ALLOWED_TABLES or table_name not in ALLOWED_TABLES[database_id]:
        return []
    
    return ALLOWED_TABLES[database_id][table_name]["columns"]

def is_table_allowed(database_id: str, table_name: str) -> bool:
    """Check if table access is allowed"""
    return database_id in ALLOWED_TABLES and table_name in ALLOWED_TABLES[database_id]

def execute_query(sql: str, params: Dict = None) -> Dict:
    """Execute SQL query and return results"""
    try:
        conn = get_connection_DSSB_APP()
        cursor = conn.cursor()
        
        # Execute query
        if params:
            cursor.execute(sql, params)
        else:
            cursor.execute(sql)
        
        # Get column names
        columns = [desc[0].lower() for desc in cursor.description] if cursor.description else []
        
        # Fetch results
        rows = cursor.fetchall()
        
        # Convert to list of dictionaries
        data = []
        for row in rows:
            row_dict = {}
            for i, value in enumerate(row):
                # Handle different Oracle data types
                if isinstance(value, cx_Oracle.LOB):
                    value = value.read() if value else None
                elif hasattr(value, 'isoformat'):  # Date/DateTime
                    value = value.isoformat()
                row_dict[columns[i]] = value
            data.append(row_dict)
        
        cursor.close()
        conn.close()
        
        return {
            "success": True,
            "columns": columns,
            "data": data,
            "row_count": len(data),
            "message": "Запрос выполнен успешно"
        }
        
    except Exception as e:
        print(f"Query execution error: {e}")
        return {
            "success": False,
            "message": f"Database query failed: {str(e)}",
            "error": str(e)
        }

# Theory Management Functions
def get_next_sc_campaign_id():
    """Get next available SC campaign ID in format SC00000001, SC00000002, etc."""
    try:
        connection = get_connection_DSSB_APP()
        cursor = connection.cursor()
        
        # Find the highest SC campaign number
        cursor.execute("""
        SELECT NVL(MAX(
            CASE 
                WHEN REGEXP_LIKE(theory_id, '^SC[0-9]{8}\.[0-9]+$') THEN 
                    TO_NUMBER(SUBSTR(theory_id, 3, 8))
                ELSE 0
            END
        ), 0) + 1 as next_campaign_id
        FROM SoftCollection_theories
        """)
        result = cursor.fetchone()
        next_campaign_num = result[0] if result else 1
        
        cursor.close()
        connection.close()
        
        # Format as SC00000001, SC00000002, etc.
        return f"SC{next_campaign_num:08d}"
        
    except Exception as e:
        print(f"Error getting next SC campaign ID: {e}")
        # Return a safe default
        return "SC00000001"

def get_next_theory_id():
    """Get next available theory ID for backward compatibility (numeric format)"""
    try:
        connection = get_connection_DSSB_APP()
        cursor = connection.cursor()
        
        # Since theory_id is now VARCHAR2, we need to find the highest numeric base ID
        # This handles both old numeric IDs (1, 2, 3) and new decimal IDs (4.1, 4.2, 4.3)
        # but excludes SC format IDs
        cursor.execute("""
        SELECT NVL(MAX(
            CASE 
                WHEN REGEXP_LIKE(theory_id, '^[0-9]+(\.[0-9]+)?$') THEN
                    CASE 
                        WHEN INSTR(theory_id, '.') > 0 THEN 
                            TO_NUMBER(SUBSTR(theory_id, 1, INSTR(theory_id, '.') - 1))
                        ELSE 
                            TO_NUMBER(theory_id)
                    END
                ELSE 0
            END
        ), 0) + 1 
        FROM SoftCollection_theories
        WHERE REGEXP_LIKE(theory_id, '^[0-9]+(\.[0-9]+)?$')
        """)
        result = cursor.fetchone()
        next_id = result[0] if result else 1
        
        cursor.close()
        connection.close()
        
        return int(next_id)
        
    except Exception as e:
        print(f"Error getting next theory ID: {e}")
        # Return a safe default
        return 1

def create_theory_with_custom_id(theory_name, theory_description, theory_start_date, theory_end_date, user_iins, created_by, custom_theory_id):
    """Create a new campaign record with a custom theory ID (for stratification sub-IDs)"""
    try:
        connection = get_connection_DSSB_APP()
        cursor = connection.cursor()
        
        # Count unique users (remove duplicates and empty values)
        unique_users = set()
        for iin in user_iins:
            if iin and str(iin).strip():
                unique_users.add(str(iin).strip())
        user_count = len(unique_users)
        
        # Insert single campaign record
        insert_sql = """
        INSERT INTO SoftCollection_theories 
        (theory_id, theory_name, theory_description, load_date, theory_start_date, theory_end_date, user_count, created_by)
        VALUES (:1, :2, :3, SYSDATE, TO_DATE(:4, 'YYYY-MM-DD'), TO_DATE(:5, 'YYYY-MM-DD'), :6, :7)
        """
        
        cursor.execute(insert_sql, (
            custom_theory_id,
            theory_name, 
            theory_description,
            theory_start_date,
            theory_end_date,
            user_count,
            created_by
        ))
        
        connection.commit()
        cursor.close()
        connection.close()
        
        return {
            "success": True,
            "message": f"Campaign '{theory_name}' created successfully with ID {custom_theory_id}",
            "theory_id": custom_theory_id,
            "users_added": user_count
        }
        
    except Exception as e:
        print(f"Error creating campaign with custom ID: {e}")
        return {
            "success": False,
            "message": f"Failed to create campaign: {str(e)}"
        }

def create_theory(theory_name, theory_description, theory_start_date, theory_end_date, user_iins, created_by):
    """Create a new campaign with user assignments (backward compatibility - uses numeric ID)"""
    try:
        connection = get_connection_DSSB_APP()
        cursor = connection.cursor()
        
        # Get next theory ID
        theory_id = get_next_theory_id()
        
        # Count unique users (remove duplicates and empty values)
        unique_users = set()
        for iin in user_iins:
            if iin and str(iin).strip():
                unique_users.add(str(iin).strip())
        user_count = len(unique_users)
        
        # Insert single campaign record
        insert_sql = """
        INSERT INTO SoftCollection_theories 
        (theory_id, theory_name, theory_description, load_date, theory_start_date, theory_end_date, user_count, created_by)
        VALUES (:1, :2, :3, SYSDATE, TO_DATE(:4, 'YYYY-MM-DD'), TO_DATE(:5, 'YYYY-MM-DD'), :6, :7)
        """
        
        cursor.execute(insert_sql, (
            theory_id,
            theory_name, 
            theory_description,
            theory_start_date,
            theory_end_date,
            user_count,
            created_by
        ))
        
        connection.commit()
        cursor.close()
        connection.close()
        
        return {
            "success": True,
            "message": f"Campaign '{theory_name}' created successfully",
            "theory_id": theory_id,
            "users_added": user_count
        }
        
    except Exception as e:
        print(f"Error creating campaign: {e}")
        return {
            "success": False,
            "message": f"Failed to create campaign: {str(e)}"
        }

def get_active_theories():
    """Get all campaign records with enhanced sorting for both numeric and SC formats"""
    try:
        connection = get_connection_DSSB_APP()
        cursor = connection.cursor()
        
        # Get all campaign records - much simpler now with one record per campaign
        query = """
        SELECT 
            theory_id,
            theory_name,
            theory_description,
            TO_CHAR(load_date, 'YYYY-MM-DD') as load_date,
            TO_CHAR(theory_start_date, 'YYYY-MM-DD') as theory_start_date,
            TO_CHAR(theory_end_date, 'YYYY-MM-DD') as theory_end_date,
            user_count,
            CASE WHEN SYSDATE BETWEEN theory_start_date AND theory_end_date THEN 1 ELSE 0 END as is_active,
            created_by
        FROM SoftCollection_theories
        ORDER BY 
            theory_start_date DESC,
            CASE 
                -- SC format sorting (SC00000001.1, SC00000001.2, etc.)
                WHEN REGEXP_LIKE(theory_id, '^SC[0-9]{8}\.[0-9]+$') THEN
                    TO_NUMBER(SUBSTR(theory_id, 3, 8)) * 1000 + TO_NUMBER(SUBSTR(theory_id, INSTR(theory_id, '.') + 1))
                -- Numeric format sorting (1, 2, 3, 1.1, 1.2, etc.)
                WHEN REGEXP_LIKE(theory_id, '^[0-9]+(\.[0-9]+)?$') THEN
                    CASE 
                        WHEN INSTR(theory_id, '.') > 0 THEN 
                            TO_NUMBER(SUBSTR(theory_id, 1, INSTR(theory_id, '.') - 1)) * 1000 + 
                            TO_NUMBER(SUBSTR(theory_id, INSTR(theory_id, '.') + 1))
                        ELSE 
                            TO_NUMBER(theory_id) * 1000
                    END
                -- Other formats go to the end
                ELSE 999999999
            END DESC,
            theory_id DESC
        """
        
        cursor.execute(query)
        columns = [desc[0].lower() for desc in cursor.description]
        
        theories = []
        for row in cursor.fetchall():
            theory_dict = dict(zip(columns, row))
            theory_dict['is_active'] = bool(theory_dict['is_active'])
            theories.append(theory_dict)
        
        cursor.close()
        connection.close()
        
        return {
            "success": True,
            "data": theories,
            "message": f"Retrieved {len(theories)} campaigns"
        }
        
    except Exception as e:
        print(f"Error getting campaigns: {e}")
        return {
            "success": False,
            "data": [],
            "message": f"Failed to get campaigns: {str(e)}"
        }

def detect_iin_columns(data):
    """Detect IIN or IIN_BIN columns in query results"""
    if not data or len(data) == 0:
        return None
    
    # Check column names for IIN-like patterns
    first_row = data[0]
    for column_name in first_row.keys():
        column_upper = column_name.upper()
        if 'IIN' in column_upper or 'IIN_BIN' in column_upper:
            return column_name
    
    return None

def extract_iin_values(data, iin_column):
    """Extract unique IIN values from query results"""
    if not data or not iin_column:
        return []
    
    iin_values = set()
    for row in data:
        iin_value = row.get(iin_column)
        if iin_value and str(iin_value).strip():
            iin_values.add(str(iin_value).strip())
    
    return list(iin_values)

# SC Local Tables Management Functions
def insert_control_group(theory_id, iin_values, date_start, date_end, additional_fields=None):
    """Insert control group users into SC_local_control table"""
    try:
        connection = get_connection_DSSB_APP()
        cursor = connection.cursor()
        
        # Prepare additional fields (tab1-tab5)
        tab_fields = additional_fields or {}
        tab1 = tab_fields.get('tab1', None)
        tab2 = tab_fields.get('tab2', None)
        tab3 = tab_fields.get('tab3', None)
        tab4 = tab_fields.get('tab4', None)
        tab5 = tab_fields.get('tab5', None)
        
        insert_sql = """
        INSERT INTO SC_local_control 
        (IIN, THEORY_ID, date_start, date_end, insert_datetime, tab1, tab2, tab3, tab4, tab5)
        VALUES (:1, :2, TO_DATE(:3, 'YYYY-MM-DD'), TO_DATE(:4, 'YYYY-MM-DD'), SYSDATE, :5, :6, :7, :8, :9)
        """
        
        inserted_count = 0
        for iin in iin_values:
            try:
                cursor.execute(insert_sql, (
                    str(iin).strip(),
                    theory_id,
                    date_start,
                    date_end,
                    tab1, tab2, tab3, tab4, tab5
                ))
                inserted_count += 1
            except Exception as e:
                print(f"Error inserting control IIN {iin}: {e}")
                continue
        
        connection.commit()
        cursor.close()
        connection.close()
        
        return {
            "success": True,
            "inserted_count": inserted_count,
            "message": f"Inserted {inserted_count} users into control group"
        }
        
    except Exception as e:
        print(f"Error inserting control group: {e}")
        return {
            "success": False,
            "message": f"Failed to insert control group: {str(e)}"
        }

def insert_into_spss_theory_users(theory_id, iin_values, date_start, date_end, additional_fields=None):
    """Insert target group users into SC_theory_users table in SPSS database"""
    try:
        connection = get_connection_SPSS()
        cursor = connection.cursor()
        
        # Prepare additional fields (tab1-tab5)
        tab_fields = additional_fields or {}
        tab1 = tab_fields.get('tab1', None)
        tab2 = tab_fields.get('tab2', None)
        tab3 = tab_fields.get('tab3', None)
        tab4 = tab_fields.get('tab4', None)
        tab5 = tab_fields.get('tab5', None)
        
        insert_sql = """
        INSERT INTO SC_theory_users 
        (IIN, THEORY_ID, date_start, date_end, insert_datetime, tab1, tab2, tab3, tab4, tab5)
        VALUES (:1, :2, TO_DATE(:3, 'YYYY-MM-DD'), TO_DATE(:4, 'YYYY-MM-DD'), SYSDATE, :5, :6, :7, :8, :9)
        """
        
        inserted_count = 0
        for iin in iin_values:
            try:
                cursor.execute(insert_sql, (
                    str(iin).strip(),
                    theory_id,
                    date_start,
                    date_end,
                    tab1, tab2, tab3, tab4, tab5
                ))
                inserted_count += 1
            except Exception as e:
                print(f"Error inserting target IIN {iin} into SPSS: {e}")
                continue
        
        connection.commit()
        cursor.close()
        connection.close()
        
        return {
            "success": True,
            "inserted_count": inserted_count,
            "message": f"Inserted {inserted_count} users into SPSS SC_theory_users table"
        }
        
    except Exception as e:
        print(f"Error inserting into SPSS SC_theory_users: {e}")
        return {
            "success": False,
            "message": f"Failed to insert into SPSS SC_theory_users: {str(e)}"
        }

def insert_target_groups(theory_id, iin_values, date_start, date_end, additional_fields=None):
    """Insert target group users into SC_local_target table and duplicate to SPSS SC_theory_users table"""
    results = {
        "dssb_app": None,
        "spss": None,
        "overall_success": False,
        "total_inserted": 0,
        "messages": []
    }
    
    # Prepare additional fields (tab1-tab5)
    tab_fields = additional_fields or {}
    tab1 = tab_fields.get('tab1', None)
    tab2 = tab_fields.get('tab2', None)
    tab3 = tab_fields.get('tab3', None)
    tab4 = tab_fields.get('tab4', None)
    tab5 = tab_fields.get('tab5', None)
    
    # 1. Insert into DSSB_APP SC_local_target table
    try:
        connection = get_connection_DSSB_APP()
        cursor = connection.cursor()
        
        insert_sql = """
        INSERT INTO SC_local_target 
        (IIN, THEORY_ID, date_start, date_end, insert_datetime, tab1, tab2, tab3, tab4, tab5)
        VALUES (:1, :2, TO_DATE(:3, 'YYYY-MM-DD'), TO_DATE(:4, 'YYYY-MM-DD'), SYSDATE, :5, :6, :7, :8, :9)
        """
        
        dssb_inserted_count = 0
        for iin in iin_values:
            try:
                cursor.execute(insert_sql, (
                    str(iin).strip(),
                    theory_id,
                    date_start,
                    date_end,
                    tab1, tab2, tab3, tab4, tab5
                ))
                dssb_inserted_count += 1
            except Exception as e:
                print(f"Error inserting target IIN {iin} into DSSB_APP: {e}")
                continue
        
        connection.commit()
        cursor.close()
        connection.close()
        
        results["dssb_app"] = {
            "success": True,
            "inserted_count": dssb_inserted_count,
            "message": f"Inserted {dssb_inserted_count} users into DSSB_APP SC_local_target"
        }
        results["total_inserted"] += dssb_inserted_count
        results["messages"].append(f"DSSB_APP: {dssb_inserted_count} users inserted into SC_local_target")
        
    except Exception as e:
        print(f"Error inserting target groups into DSSB_APP: {e}")
        results["dssb_app"] = {
            "success": False,
            "message": f"Failed to insert into DSSB_APP SC_local_target: {str(e)}"
        }
        results["messages"].append(f"DSSB_APP Error: {str(e)}")
    
    # 2. Duplicate insert into SPSS SC_theory_users table
    try:
        spss_result = insert_into_spss_theory_users(theory_id, iin_values, date_start, date_end, additional_fields)
        results["spss"] = spss_result
        
        if spss_result["success"]:
            results["total_inserted"] += spss_result["inserted_count"]
            results["messages"].append(f"SPSS: {spss_result['inserted_count']} users inserted into SC_theory_users")
        else:
            results["messages"].append(f"SPSS Error: {spss_result['message']}")
            
    except Exception as e:
        print(f"Error duplicating to SPSS: {e}")
        results["spss"] = {
            "success": False,
            "message": f"Failed to duplicate to SPSS: {str(e)}"
        }
        results["messages"].append(f"SPSS Error: {str(e)}")
    
    # Determine overall success
    dssb_success = results["dssb_app"] and results["dssb_app"]["success"]
    spss_success = results["spss"] and results["spss"]["success"]
    
    # Overall success if at least DSSB_APP succeeded (SPSS is bonus)
    results["overall_success"] = dssb_success
    
    # Create consolidated response
    if dssb_success and spss_success:
        message = f"Successfully inserted into both databases: {results['messages'][0]}, {results['messages'][1]}"
    elif dssb_success:
        message = f"Primary insertion successful: {results['messages'][0]}. SPSS duplication failed: {results['messages'][1] if len(results['messages']) > 1 else 'Unknown error'}"
    else:
        message = f"Primary insertion failed: {results['messages'][0] if results['messages'] else 'Unknown error'}"
    
    return {
        "success": results["overall_success"],
        "inserted_count": results["dssb_app"]["inserted_count"] if results["dssb_app"] and results["dssb_app"]["success"] else 0,
        "message": message,
        "detailed_results": results
    }

def get_sc_local_data(table_name, theory_id=None):
    """Get data from SC_local_control or SC_local_target tables"""
    try:
        connection = get_connection_DSSB_APP()
        cursor = connection.cursor()
        
        # Validate table name for security
        if table_name not in ['SC_local_control', 'SC_local_target']:
            raise ValueError("Invalid table name")
        
        base_query = f"""
        SELECT IIN, THEORY_ID, 
               TO_CHAR(date_start, 'YYYY-MM-DD') as date_start,
               TO_CHAR(date_end, 'YYYY-MM-DD') as date_end,
               TO_CHAR(insert_datetime, 'YYYY-MM-DD HH24:MI:SS') as insert_datetime,
               tab1, tab2, tab3, tab4, tab5
        FROM {table_name}
        """
        
        if theory_id:
            query = base_query + " WHERE THEORY_ID = :1 ORDER BY insert_datetime DESC"
            cursor.execute(query, (theory_id,))
        else:
            query = base_query + " ORDER BY insert_datetime DESC"
            cursor.execute(query)
        
        columns = [desc[0].lower() for desc in cursor.description]
        
        data = []
        for row in cursor.fetchall():
            data.append(dict(zip(columns, row)))
        
        cursor.close()
        connection.close()
        
        return {
            "success": True,
            "data": data,
            "message": f"Retrieved {len(data)} records from {table_name}"
        }
        
    except Exception as e:
        print(f"Error getting SC local data: {e}")
        return {
            "success": False,
            "data": [],
            "message": f"Failed to get data: {str(e)}"
        } 