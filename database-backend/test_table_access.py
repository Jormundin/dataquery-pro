#!/usr/bin/env python3
"""
Тестовый скрипт для проверки доступа к таблицам Oracle
"""

from database import get_databases, get_tables, get_table_columns, is_table_allowed
from query_builder import QueryBuilder

def test_table_access():
    """Тест доступа к таблицам"""
    print("🧪 Тест доступа к таблицам Oracle")
    print("=" * 50)
    
    # Тест 1: Получение списка БД
    print("\n1. Тест получения списка баз данных:")
    databases = get_databases()
    print(f"   Найдено БД: {len(databases)}")
    for db in databases:
        print(f"   - {db['id']}: {db['name']}")
    
    # Тест 2: Получение списка таблиц
    print("\n2. Тест получения списка таблиц для DSSB_APP:")
    tables = get_tables('DSSB_APP')
    print(f"   Найдено таблиц: {len(tables)}")
    for table in tables:
        print(f"   - {table['name']}: {table['description']}")
    
    # Тест 3: Проверка доступа к таблице
    print("\n3. Тест доступа к DSSB_DM.RB_CLIENTS:")
    table_name = 'DSSB_DM.RB_CLIENTS'
    is_allowed = is_table_allowed('DSSB_APP', table_name)
    print(f"   Доступ к {table_name}: {'✅ РАЗРЕШЕН' if is_allowed else '❌ ЗАПРЕЩЕН'}")
    
    # Тест 4: Получение столбцов таблицы
    print("\n4. Тест получения столбцов для DSSB_DM.RB_CLIENTS:")
    columns = get_table_columns('DSSB_APP', table_name)
    print(f"   Найдено столбцов: {len(columns)}")
    for col in columns:
        print(f"   - {col['name']} ({col['type']}): {col['description']}")
    
    # Тест 5: QueryBuilder
    print("\n5. Тест QueryBuilder:")
    query_builder = QueryBuilder()
    
    try:
        # Тест построения запроса
        request_data = {
            'database_id': 'DSSB_APP',
            'table': 'DSSB_DM.RB_CLIENTS',
            'columns': ['FIRST_NAME', 'LAST_NAME'],
            'filters': [
                {'column': 'FIRST_NAME', 'operator': 'equals', 'value': 'Test'}
            ],
            'sort_by': 'FIRST_NAME',
            'sort_order': 'ASC',
            'limit': 10
        }
        
        sql_query = query_builder.build_query(request_data)
        print(f"   Сгенерированный SQL: {sql_query}")
        print("   ✅ QueryBuilder работает корректно")
    except Exception as e:
        print(f"   ❌ Ошибка QueryBuilder: {str(e)}")
    
    print("\n" + "=" * 50)
    print("✅ Тестирование завершено!")

if __name__ == "__main__":
    test_table_access() 