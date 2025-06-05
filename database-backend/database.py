import os
import cx_Oracle
from typing import List, Dict, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Hardcoded list of allowed tables for security
ALLOWED_TABLES = {
    'dssb_app': {
        # Real Oracle tables with schema prefix
        'DSSB_DM.RB_CLIENTS': {
            'description': 'Клиенты банка',
            'columns': [
                {'name': 'CLIENT_ID', 'type': 'NUMBER', 'description': 'ID клиента'},
                {'name': 'CLIENT_NAME', 'type': 'VARCHAR2', 'description': 'Имя клиента'},
                {'name': 'CLIENT_TYPE', 'type': 'VARCHAR2', 'description': 'Тип клиента'},
                {'name': 'REGISTRATION_DATE', 'type': 'DATE', 'description': 'Дата регистрации'},
                {'name': 'STATUS', 'type': 'VARCHAR2', 'description': 'Статус'}
            ]
        },
        'DSSB_DM.RB_ACCOUNTS': {
            'description': 'Банковские счета',
            'columns': [
                {'name': 'ACCOUNT_ID', 'type': 'NUMBER', 'description': 'ID счета'},
                {'name': 'CLIENT_ID', 'type': 'NUMBER', 'description': 'ID клиента'},
                {'name': 'ACCOUNT_NUMBER', 'type': 'VARCHAR2', 'description': 'Номер счета'},
                {'name': 'ACCOUNT_TYPE', 'type': 'VARCHAR2', 'description': 'Тип счета'},
                {'name': 'BALANCE', 'type': 'NUMBER', 'description': 'Баланс'},
                {'name': 'CURRENCY', 'type': 'VARCHAR2', 'description': 'Валюта'},
                {'name': 'OPEN_DATE', 'type': 'DATE', 'description': 'Дата открытия'},
                {'name': 'STATUS', 'type': 'VARCHAR2', 'description': 'Статус счета'}
            ]
        },
        'DSSB_DM.RB_TRANSACTIONS': {
            'description': 'Банковские операции',
            'columns': [
                {'name': 'TRANSACTION_ID', 'type': 'NUMBER', 'description': 'ID операции'},
                {'name': 'ACCOUNT_ID', 'type': 'NUMBER', 'description': 'ID счета'},
                {'name': 'TRANSACTION_DATE', 'type': 'DATE', 'description': 'Дата операции'},
                {'name': 'AMOUNT', 'type': 'NUMBER', 'description': 'Сумма'},
                {'name': 'TRANSACTION_TYPE', 'type': 'VARCHAR2', 'description': 'Тип операции'},
                {'name': 'DESCRIPTION', 'type': 'VARCHAR2', 'description': 'Описание'},
                {'name': 'STATUS', 'type': 'VARCHAR2', 'description': 'Статус операции'}
            ]
        },
        'DSSB_DM.RB_PRODUCTS': {
            'description': 'Банковские продукты',
            'columns': [
                {'name': 'PRODUCT_ID', 'type': 'NUMBER', 'description': 'ID продукта'},
                {'name': 'PRODUCT_NAME', 'type': 'VARCHAR2', 'description': 'Название продукта'},
                {'name': 'PRODUCT_TYPE', 'type': 'VARCHAR2', 'description': 'Тип продукта'},
                {'name': 'INTEREST_RATE', 'type': 'NUMBER', 'description': 'Процентная ставка'},
                {'name': 'MIN_AMOUNT', 'type': 'NUMBER', 'description': 'Минимальная сумма'},
                {'name': 'MAX_AMOUNT', 'type': 'NUMBER', 'description': 'Максимальная сумма'},
                {'name': 'CURRENCY', 'type': 'VARCHAR2', 'description': 'Валюта'},
                {'name': 'STATUS', 'type': 'VARCHAR2', 'description': 'Статус продукта'}
            ]
        },
        'DSSB_DM.RB_REPORTS': {
            'description': 'Отчеты',
            'columns': [
                {'name': 'REPORT_ID', 'type': 'NUMBER', 'description': 'ID отчета'},
                {'name': 'REPORT_NAME', 'type': 'VARCHAR2', 'description': 'Название отчета'},
                {'name': 'REPORT_TYPE', 'type': 'VARCHAR2', 'description': 'Тип отчета'},
                {'name': 'CREATION_DATE', 'type': 'DATE', 'description': 'Дата создания'},
                {'name': 'REPORT_DATA', 'type': 'CLOB', 'description': 'Данные отчета'},
                {'name': 'STATUS', 'type': 'VARCHAR2', 'description': 'Статус отчета'}
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
        return {
            "success": False,
            "error": str(e),
            "message": f"Ошибка выполнения запроса: {str(e)}"
        } 