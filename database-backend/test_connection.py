#!/usr/bin/env python3
"""
Тестирование подключения к Oracle базе данных
Запустите этот скрипт для проверки настроек подключения перед запуском основного приложения
"""

import os
import sys
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

def test_oracle_import():
    """Тестирование импорта cx_Oracle"""
    try:
        import cx_Oracle
        print("✅ cx_Oracle успешно импортирован")
        print(f"   Версия: {cx_Oracle.version}")
        print(f"   Client версия: {cx_Oracle.clientversion()}")
        return True
    except ImportError as e:
        print("❌ Ошибка импорта cx_Oracle:")
        print(f"   {e}")
        print("\n💡 Решение:")
        print("   1. Установите Oracle Instant Client")
        print("   2. Выполните: pip install cx_Oracle")
        return False
    except Exception as e:
        print(f"❌ Ошибка при проверке cx_Oracle: {e}")
        return False

def test_environment_variables():
    """Проверка переменных окружения"""
    required_vars = ['ORACLE_HOST', 'ORACLE_SID', 'ORACLE_USER', 'ORACLE_PASSWORD']
    missing_vars = []
    
    print("\n🔧 Проверка переменных окружения:")
    for var in required_vars:
        value = os.getenv(var)
        if value:
            if var == 'ORACLE_PASSWORD':
                print(f"   {var}: {'*' * len(value)}")
            else:
                print(f"   {var}: {value}")
        else:
            missing_vars.append(var)
            print(f"   {var}: ❌ НЕ ЗАДАНА")
    
    if missing_vars:
        print(f"\n❌ Отсутствуют обязательные переменные: {', '.join(missing_vars)}")
        print("💡 Создайте файл .env на основе env_example.txt")
        return False
    
    print("✅ Все переменные окружения настроены")
    return True

def test_database_connection():
    """Тестирование подключения к базе данных"""
    try:
        from database import get_connection_DSSB_APP
        
        print("\n🔌 Тестирование подключения к базе данных...")
        
        conn = get_connection_DSSB_APP()
        cursor = conn.cursor()
        
        # Выполняем простой тестовый запрос
        cursor.execute("SELECT 1 FROM DUAL")
        result = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if result and result[0] == 1:
            print("✅ Подключение к базе данных успешно!")
            return True
        else:
            print("❌ Неожиданный результат тестового запроса")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка подключения к базе данных:")
        print(f"   {e}")
        print("\n💡 Возможные причины:")
        print("   1. Неверные учетные данные")
        print("   2. Недоступен сервер базы данных")
        print("   3. Неправильно указан SID/Service Name")
        print("   4. Блокировка файрволом")
        return False

def test_tables_access():
    """Тестирование доступа к таблицам"""
    try:
        from database import ALLOWED_TABLES, get_connection_DSSB_APP
        
        print("\n📊 Проверка доступа к таблицам...")
        
        conn = get_connection_DSSB_APP()
        cursor = conn.cursor()
        
        for db_name, tables in ALLOWED_TABLES.items():
            print(f"\n   База данных: {db_name}")
            for table_name in tables.keys():
                try:
                    # Проверяем существование таблицы
                    cursor.execute(f"SELECT COUNT(*) FROM {table_name.upper()} WHERE ROWNUM <= 1")
                    result = cursor.fetchone()
                    print(f"   ✅ {table_name}: доступна")
                except Exception as e:
                    print(f"   ⚠️  {table_name}: {e}")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при проверке таблиц: {e}")
        return False

def main():
    """Основная функция тестирования"""
    print("🧪 DataQuery Pro - Тестирование подключения к Oracle Database")
    print("=" * 65)
    
    all_tests_passed = True
    
    # Тест 1: Импорт cx_Oracle
    if not test_oracle_import():
        all_tests_passed = False
        print("\n❌ Тестирование прервано из-за проблем с cx_Oracle")
        sys.exit(1)
    
    # Тест 2: Переменные окружения
    if not test_environment_variables():
        all_tests_passed = False
        print("\n❌ Тестирование прервано из-за отсутствующих переменных")
        sys.exit(1)
    
    # Тест 3: Подключение к БД
    if not test_database_connection():
        all_tests_passed = False
    
    # Тест 4: Доступ к таблицам
    if all_tests_passed:
        if not test_tables_access():
            all_tests_passed = False
    
    print("\n" + "=" * 65)
    if all_tests_passed:
        print("🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
        print("   Можно запускать основное приложение: python main.py")
    else:
        print("⚠️  ОБНАРУЖЕНЫ ПРОБЛЕМЫ!")
        print("   Исправьте ошибки перед запуском приложения")
        sys.exit(1)

if __name__ == "__main__":
    main() 