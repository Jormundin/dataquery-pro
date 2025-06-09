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
            'description': 'Информация о теориях Soft Collection',
            'columns': [
                {'name': 'IIN', 'type': 'VARCHAR2', 'description': 'ID'},
                {'name': 'THEORY_NAME', 'type': 'VARCHAR2', 'description': 'ID'},
                {'name': 'THEORY_DESCRIPTION', 'type': 'VARCHAR2', 'description': 'ID'},
                {'name': 'LOAD_DATE', 'type': 'DATE', 'description': 'ID'},
                {'name': 'THEORY_START_DATE', 'type': 'DATE', 'description': 'ID'},
                {'name': 'THEORY_END_DATE', 'type': 'DATE', 'description': 'NAME'},
                {'name': 'THEORY_ID', 'type': 'VARCHAR2', 'description': 'NAME'},
                {'name': 'CREATED_BY', 'type': 'VARCHAR2', 'description': 'NAME'},
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
            "message": "Соединение с базой данных установлено успешно",
            "connected": True
        }
    except Exception as e:
        return {
            "status": "error", 
            "message": f"Ошибка подключения к базе данных: {str(e)}",
            "connected": False
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
def get_next_theory_id():
    """Get next available theory ID"""
    try:
        connection = get_connection_DSSB_APP()
        cursor = connection.cursor()
        
        cursor.execute("SELECT NVL(MAX(theory_id), 0) + 1 FROM SoftCollection_theories")
        result = cursor.fetchone()
        next_id = result[0] if result else 1
        
        cursor.close()
        connection.close()
        
        return next_id
        
    except Exception as e:
        print(f"Error getting next theory ID: {e}")
        # Return 1 if table doesn't exist yet
        return 1

def create_theory(theory_name, theory_description, theory_start_date, theory_end_date, user_iins, created_by):
    """Create a new theory with user assignments"""
    try:
        connection = get_connection_DSSB_APP()
        cursor = connection.cursor()
        
        # Get next theory ID
        theory_id = get_next_theory_id()
        
        # Insert theory records for each user
        insert_sql = """
        INSERT INTO SoftCollection_theories 
        (IIN, theory_name, theory_description, load_date, theory_start_date, theory_end_date, theory_id, created_by)
        VALUES (:1, :2, :3, SYSDATE, TO_DATE(:4, 'YYYY-MM-DD'), TO_DATE(:5, 'YYYY-MM-DD'), :6, :7)
        """
        
        users_added = 0
        for iin in user_iins:
            try:
                cursor.execute(insert_sql, (
                    iin, 
                    theory_name, 
                    theory_description,
                    theory_start_date,
                    theory_end_date,
                    theory_id,
                    created_by
                ))
                users_added += 1
            except Exception as e:
                print(f"Error inserting IIN {iin}: {e}")
                continue
        
        connection.commit()
        cursor.close()
        connection.close()
        
        return {
            "success": True,
            "message": f"Theory '{theory_name}' created successfully",
            "theory_id": theory_id,
            "users_added": users_added
        }
        
    except Exception as e:
        print(f"Error creating theory: {e}")
        return {
            "success": False,
            "message": f"Failed to create theory: {str(e)}"
        }

def get_active_theories():
    """Get all currently active theories"""
    try:
        connection = get_connection_DSSB_APP()
        cursor = connection.cursor()
        
        # Get theories that are currently active
        query = """
        SELECT 
            theory_id,
            theory_name,
            theory_description,
            TO_CHAR(MIN(load_date), 'YYYY-MM-DD') as load_date,
            TO_CHAR(theory_start_date, 'YYYY-MM-DD') as theory_start_date,
            TO_CHAR(theory_end_date, 'YYYY-MM-DD') as theory_end_date,
            COUNT(*) as user_count,
            CASE WHEN SYSDATE BETWEEN theory_start_date AND theory_end_date THEN 1 ELSE 0 END as is_active,
            MAX(created_by) as created_by
        FROM SoftCollection_theories
        GROUP BY theory_id, theory_name, theory_description, theory_start_date, theory_end_date
        ORDER BY theory_start_date DESC
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
            "message": f"Retrieved {len(theories)} theories"
        }
        
    except Exception as e:
        print(f"Error getting active theories: {e}")
        return {
            "success": False,
            "data": [],
            "message": f"Failed to get theories: {str(e)}"
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