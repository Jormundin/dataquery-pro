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
    print("\n2. Тест получения списка таблиц для dssb_app:")
    tables = get_tables('dssb_app')
    print(f"   Найдено таблиц: {len(tables)}")
    for table in tables:
        print(f"   - {table['name']}: {table['description']}")
    
    # Тест 3: Проверка доступа к DSSB_DM.RB_CLIENTS
    print("\n3. Тест доступа к DSSB_DM.RB_CLIENTS:")
    table_name = 'DSSB_DM.RB_CLIENTS'
    is_allowed = is_table_allowed('dssb_app', table_name)
    print(f"   Доступ к {table_name}: {'✅ РАЗРЕШЕН' if is_allowed else '❌ ЗАПРЕЩЕН'}")
    
    # Тест 4: Получение столбцов таблицы
    print("\n4. Тест получения столбцов DSSB_DM.RB_CLIENTS:")
    columns = get_table_columns('dssb_app', table_name)
    print(f"   Найдено столбцов: {len(columns)}")
    for col in columns:
        print(f"   - {col['name']} ({col['type']}): {col['description']}")
    
    # Тест 5: QueryBuilder
    print("\n5. Тест QueryBuilder:")
    query_builder = QueryBuilder()
    
    try:
        # Тест санитизации имени таблицы
        sanitized = query_builder.sanitize_identifier(table_name)
        print(f"   Санитизация {table_name}: {sanitized} ✅")
        
        # Тест построения простого запроса
        request_data = {
            'database_id': 'DSSB_APP',
            'table': table_name,
            'limit': 10
        }
        
        sql = query_builder.build_query(request_data)
        print(f"   Сгенерированный SQL:")
        print(f"   {sql}")
        print("   ✅ QueryBuilder работает корректно")
        
    except Exception as e:
        print(f"   ❌ Ошибка QueryBuilder: {str(e)}")
    
    print("\n" + "=" * 50)
    print("✅ Тестирование завершено!")

if __name__ == "__main__":
    test_table_access() 