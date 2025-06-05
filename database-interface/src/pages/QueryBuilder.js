import React, { useState, useEffect } from 'react';
import { 
  Plus, 
  Trash2, 
  Play, 
  Database, 
  Filter,
  Download,
  RefreshCw
} from 'lucide-react';
import { databaseAPI, queryBuilder } from '../services/api';

const QueryBuilder = () => {
  const [selectedDatabase, setSelectedDatabase] = useState('');
  const [selectedTable, setSelectedTable] = useState('');
  const [columns, setColumns] = useState([]);
  const [selectedColumns, setSelectedColumns] = useState([]);
  const [filters, setFilters] = useState([]);
  const [sortBy, setSortBy] = useState('');
  const [sortOrder, setSortOrder] = useState('ASC');
  const [limit, setLimit] = useState(100);
  const [isLoading, setIsLoading] = useState(false);
  const [queryResults, setQueryResults] = useState(null);
  const [databases, setDatabases] = useState([]);
  const [tables, setTables] = useState([]);
  const [error, setError] = useState(null);
  const [rowCount, setRowCount] = useState(null);
  const [isCountLoading, setIsCountLoading] = useState(false);
  const [countError, setCountError] = useState(null);

  // Theory creation state
  const [showTheoryModal, setShowTheoryModal] = useState(false);
  const [theoryData, setTheoryData] = useState({
    theory_name: '',
    theory_description: '',
    theory_start_date: '',
    theory_end_date: ''
  });
  const [iinInfo, setIinInfo] = useState(null);
  const [isCreatingTheory, setIsCreatingTheory] = useState(false);

  useEffect(() => {
    loadDatabases();
  }, []);

  useEffect(() => {
    if (selectedDatabase) {
      loadTables(selectedDatabase);
    } else {
      setTables([]);
      setSelectedTable('');
    }
  }, [selectedDatabase]);

  useEffect(() => {
    if (selectedDatabase && selectedTable) {
      loadTableColumns(selectedDatabase, selectedTable);
    } else {
      setColumns([]);
      setSelectedColumns([]);
      setFilters([]);
    }
  }, [selectedDatabase, selectedTable]);

  const loadDatabases = async () => {
    try {
      const response = await databaseAPI.getDatabases();
      setDatabases(response.data || []);
    } catch (err) {
      console.error('Error loading databases:', err);
      setError('Ошибка загрузки баз данных');
      // Fallback to mock data
      setDatabases([
        { id: 'prod', name: 'Продуктивная база данных' },
        { id: 'analytics', name: 'Аналитическая база данных' },
        { id: 'user_mgmt', name: 'Управление пользователями' },
      ]);
    }
  };

  const loadTables = async (databaseId) => {
    try {
      const response = await databaseAPI.getTables(databaseId);
      setTables(response.data || []);
    } catch (err) {
      console.error('Error loading tables:', err);
      setError('Ошибка загрузки таблиц');
      // Fallback to mock data
      const mockTables = {
        prod: [
          { name: 'customers', description: 'Информация о клиентах' },
          { name: 'orders', description: 'Записи заказов' },
          { name: 'products', description: 'Каталог продуктов' },
          { name: 'employees', description: 'Записи сотрудников' },
        ],
        analytics: [
          { name: 'sales_metrics', description: 'Данные по продажам' },
          { name: 'user_behavior', description: 'Данные взаимодействия пользователей' },
          { name: 'revenue_reports', description: 'Анализ доходов' },
        ],
        user_mgmt: [
          { name: 'users', description: 'Учетные записи пользователей' },
          { name: 'roles', description: 'Роли и права пользователей' },
          { name: 'sessions', description: 'Активные сессии пользователей' },
        ],
      };
      setTables(mockTables[databaseId] || []);
    }
  };

  const loadTableColumns = async (databaseId, tableName) => {
    try {
      const response = await databaseAPI.getTableColumns(databaseId, tableName);
      setColumns(response.data || []);
    } catch (err) {
      console.error('Error loading table columns:', err);
      setError('Ошибка загрузки столбцов таблицы');
      // Fallback to mock data
      const tableColumns = {
        customers: [
          { name: 'id', type: 'number', description: 'ID клиента' },
          { name: 'first_name', type: 'text', description: 'Имя' },
          { name: 'last_name', type: 'text', description: 'Фамилия' },
          { name: 'email', type: 'email', description: 'Адрес электронной почты' },
          { name: 'phone', type: 'text', description: 'Номер телефона' },
          { name: 'created_at', type: 'date', description: 'Дата регистрации' },
          { name: 'status', type: 'select', description: 'Статус аккаунта', options: ['активный', 'неактивный', 'заблокирован'] },
        ],
        orders: [
          { name: 'id', type: 'number', description: 'ID заказа' },
          { name: 'customer_id', type: 'number', description: 'ID клиента' },
          { name: 'total_amount', type: 'number', description: 'Общая сумма' },
          { name: 'order_date', type: 'date', description: 'Дата заказа' },
          { name: 'status', type: 'select', description: 'Статус заказа', options: ['ожидает', 'отправлен', 'доставлен', 'отменен'] },
        ],
      };
      setColumns(tableColumns[tableName] || []);
    }
  };

  const addFilter = () => {
    setFilters([...filters, {
      id: Date.now(),
      column: '',
      operator: 'equals',
      value: ''
    }]);
  };

  const updateFilter = (id, field, value) => {
    setFilters(filters.map(filter => 
      filter.id === id ? { ...filter, [field]: value } : filter
    ));
  };

  const removeFilter = (id) => {
    setFilters(filters.filter(filter => filter.id !== id));
  };

  const executeQuery = async () => {
    if (!selectedTable) {
      setError('Пожалуйста, выберите таблицу для выполнения запроса');
      return;
    }

    setIsLoading(true);
    setError(null);
    
    try {
      const queryData = {
        database_id: selectedDatabase,
        table: selectedTable,
        columns: selectedColumns.length > 0 ? selectedColumns : columns.map(col => col.name),
        filters: filters.filter(f => f.column && f.value),
        sort_by: sortBy,
        sort_order: sortOrder,
        limit
      };

      const response = await databaseAPI.executeQuery(queryData);
      
      if (response.data.success) {
        setQueryResults({
          columns: response.data.columns || queryData.columns,
          data: response.data.data || [],
          totalRows: response.data.row_count || 0,
          executionTime: response.data.execution_time || '0.000s'
        });
        
        // Check for IIN columns in results for theory creation
        if (response.data.data && response.data.data.length > 0) {
          await checkForIINColumns(response.data.data);
        }
      } else {
        setError('Ошибка выполнения запроса: ' + response.data.message);
      }
      
    } catch (err) {
      console.error('Error executing query:', err);
      setError('Ошибка выполнения запроса: ' + (err.response?.data?.detail || err.message));
      
      // Fallback to mock data if API fails
      const mockResults = {
        columns: selectedColumns.length > 0 ? selectedColumns : columns.map(col => col.name),
        data: [
          { id: 1, first_name: 'Иван', last_name: 'Петров', email: 'ivan@example.com', status: 'активный' },
          { id: 2, first_name: 'Мария', last_name: 'Смирнова', email: 'maria@example.com', status: 'активный' },
          { id: 3, first_name: 'Алексей', last_name: 'Иванов', email: 'alex@example.com', status: 'неактивный' },
        ],
        totalRows: 3,
        executionTime: '0.045s'
      };
      
      setQueryResults(mockResults);
    } finally {
      setIsLoading(false);
    }
  };

  const getRowCount = async () => {
    if (!selectedTable) return;

    setIsCountLoading(true);
    setCountError(null);

    // Debounce timeout to avoid too many requests
    setTimeout(async () => {
      try {
        const queryData = {
          database_id: selectedDatabase,
          table: selectedTable,
          filters: filters.filter(f => f.column && f.value),
        };

        const response = await databaseAPI.getRowCount(queryData);
        
        if (response.data.success) {
          setRowCount(response.data.count);
        } else {
          setCountError(response.data.message || 'Ошибка получения количества строк');
        }
        
      } catch (err) {
        console.error('Error getting row count:', err);
        setCountError('Ошибка подсчета строк: ' + (err.response?.data?.detail || err.message));
      } finally {
        setIsCountLoading(false);
      }
    }, 500);
  };

  // Theory creation functions
  const checkForIINColumns = async (results) => {
    try {
      const response = await databaseAPI.detectIINs({ results });
      setIinInfo(response.data);
      
      if (response.data.has_iin_column) {
        // Show success message that theory creation is available
        console.log(`Обнаружена IIN колонка: ${response.data.iin_column} (${response.data.user_count} пользователей)`);
      }
    } catch (err) {
      console.error('Error detecting IIN columns:', err);
    }
  };

  const openTheoryModal = () => {
    if (!iinInfo?.has_iin_column) {
      setError('В результатах запроса не найдена IIN колонка для создания теории');
      return;
    }
    
    // Set default dates (today and one year from now)
    const today = new Date().toISOString().split('T')[0];
    const nextYear = new Date();
    nextYear.setFullYear(nextYear.getFullYear() + 1);
    const endDate = nextYear.toISOString().split('T')[0];
    
    setTheoryData({
      theory_name: '',
      theory_description: '',
      theory_start_date: today,
      theory_end_date: endDate
    });
    
    setShowTheoryModal(true);
  };

  const createTheory = async () => {
    if (!theoryData.theory_name || !theoryData.theory_start_date || !theoryData.theory_end_date) {
      setError('Пожалуйста, заполните все обязательные поля теории');
      return;
    }

    if (new Date(theoryData.theory_start_date) >= new Date(theoryData.theory_end_date)) {
      setError('Дата окончания должна быть позже даты начала');
      return;
    }

    setIsCreatingTheory(true);

    try {
      const response = await databaseAPI.createTheory({
        ...theoryData,
        user_iins: iinInfo.iin_values
      });

      if (response.data.success) {
        setShowTheoryModal(false);
        setError(null);
        alert(`Теория "${theoryData.theory_name}" создана успешно! Добавлено ${response.data.users_added} пользователей.`);
        
        // Reset theory data
        setTheoryData({
          theory_name: '',
          theory_description: '',
          theory_start_date: '',
          theory_end_date: ''
        });
      } else {
        setError('Ошибка создания теории: ' + response.data.message);
      }
    } catch (err) {
      console.error('Error creating theory:', err);
      setError('Ошибка создания теории: ' + (err.response?.data?.detail || err.message));
    } finally {
      setIsCreatingTheory(false);
    }
  };

  const generateSQL = () => {
    if (!selectedTable) return '';
    
    let sql = 'SELECT ';
    
    if (selectedColumns.length > 0) {
      sql += selectedColumns.join(', ');
    } else {
      sql += '*';
    }
    
    sql += ` FROM ${selectedTable}`;
    
    if (filters.length > 0) {
      sql += ' WHERE ';
      const conditions = filters
        .filter(f => f.column && f.value)
        .map(f => {
          const column = columns.find(c => c.name === f.column);
          let value = f.value;
          
          if (column?.type === 'text' || column?.type === 'email') {
            value = f.operator === 'contains' ? `'%${value}%'` : `'${value}'`;
          }
          
          switch (f.operator) {
            case 'equals': return `${f.column} = ${value}`;
            case 'not_equals': return `${f.column} != ${value}`;
            case 'contains': return `${f.column} LIKE ${value}`;
            case 'greater_than': return `${f.column} > ${value}`;
            case 'less_than': return `${f.column} < ${value}`;
            default: return `${f.column} = ${value}`;
          }
        });
      sql += conditions.join(' AND ');
    }
    
    if (sortBy) {
      sql += ` ORDER BY ${sortBy} ${sortOrder}`;
    }
    
    if (limit) {
      sql += ` LIMIT ${limit}`;
    }
    
    return sql;
  };

  // Auto-update count when filters change
  useEffect(() => {
    const debounceTimer = setTimeout(() => {
      if (selectedTable) {
        getRowCount();
      }
    }, 500); // 500ms debounce to avoid too many API calls

    return () => clearTimeout(debounceTimer);
  }, [selectedDatabase, selectedTable, filters]);

  return (
    <div className="query-builder">
      <div className="dashboard-header">
        <h1 className="dashboard-title">Конструктор запросов</h1>
        <p className="dashboard-subtitle">
          Создавайте запросы к базе данных без написания SQL кода
        </p>
      </div>

      {error && (
        <div className="alert alert-error" style={{ marginBottom: '1.5rem' }}>
          {error}
        </div>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem', marginBottom: '1.5rem' }}>
        {/* Database Selection */}
        <div className="card">
          <div className="card-header">
            <h2 className="card-title">
              <Database className="nav-icon" style={{ width: '20px', height: '20px', display: 'inline', marginRight: '0.5rem' }} />
              Выбор базы данных и таблицы
            </h2>
          </div>
          
          <div className="form-group">
            <label className="form-label">База данных</label>
            <select 
              className="form-select"
              value={selectedDatabase}
              onChange={(e) => {
                setSelectedDatabase(e.target.value);
                setSelectedTable('');
              }}
            >
              <option value="">Выберите базу данных...</option>
              {databases.map(db => (
                <option key={db.id} value={db.id}>{db.name}</option>
              ))}
            </select>
          </div>

          <div className="form-group">
            <label className="form-label">Таблица</label>
            <select 
              className="form-select"
              value={selectedTable}
              onChange={(e) => setSelectedTable(e.target.value)}
              disabled={!selectedDatabase}
            >
              <option value="">Выберите таблицу...</option>
              {selectedDatabase && tables.map(table => (
                <option key={table.name} value={table.name}>
                  {table.name} - {table.description}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Column Selection */}
        <div className="card">
          <div className="card-header">
            <h2 className="card-title">Столбцы для отображения</h2>
          </div>
          
          {columns.length > 0 ? (
            <div style={{ maxHeight: '200px', overflowY: 'auto' }}>
              <div style={{ marginBottom: '1rem' }}>
                <label>
                  <input
                    type="checkbox"
                    checked={selectedColumns.length === 0}
                    onChange={(e) => {
                      if (e.target.checked) {
                        setSelectedColumns([]);
                      }
                    }}
                    style={{ marginRight: '0.5rem' }}
                  />
                  <strong>Все столбцы</strong>
                </label>
              </div>
              
              {columns.map(column => (
                <div key={column.name} style={{ marginBottom: '0.5rem' }}>
                  <label>
                    <input
                      type="checkbox"
                      checked={selectedColumns.includes(column.name)}
                      onChange={(e) => {
                        if (e.target.checked) {
                          setSelectedColumns([...selectedColumns, column.name]);
                        } else {
                          setSelectedColumns(selectedColumns.filter(col => col !== column.name));
                        }
                      }}
                      style={{ marginRight: '0.5rem' }}
                    />
                    {column.name} ({column.type})
                  </label>
                  <div style={{ fontSize: '0.8rem', color: '#6b7280', marginLeft: '1.5rem' }}>
                    {column.description}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="empty-state">
              <p>Выберите таблицу для просмотра доступных столбцов</p>
            </div>
          )}
        </div>
      </div>

      {/* Filters */}
      <div className="card">
        <div className="card-header">
          <h2 className="card-title">
            <Filter className="nav-icon" style={{ width: '20px', height: '20px', display: 'inline', marginRight: '0.5rem' }} />
            Фильтры
          </h2>
          <button 
            className="btn btn-primary"
            onClick={addFilter}
            disabled={columns.length === 0}
          >
            <Plus className="nav-icon" style={{ width: '16px', height: '16px' }} />
            Добавить фильтр
          </button>
        </div>

        {filters.length > 0 ? (
          filters.map(filter => (
            <div key={filter.id} className="filter-grid">
              <select
                className="form-select"
                value={filter.column}
                onChange={(e) => updateFilter(filter.id, 'column', e.target.value)}
              >
                <option value="">Выберите столбец...</option>
                {columns.map(col => (
                  <option key={col.name} value={col.name}>{col.name}</option>
                ))}
              </select>

              <select
                className="form-select"
                value={filter.operator}
                onChange={(e) => updateFilter(filter.id, 'operator', e.target.value)}
              >
                <option value="equals">Равно</option>
                <option value="not_equals">Не равно</option>
                <option value="contains">Содержит</option>
                <option value="greater_than">Больше</option>
                <option value="less_than">Меньше</option>
              </select>

              {filter.column && columns.find(c => c.name === filter.column)?.type === 'select' ? (
                <select
                  className="form-select"
                  value={filter.value}
                  onChange={(e) => updateFilter(filter.id, 'value', e.target.value)}
                >
                  <option value="">Выберите значение...</option>
                  {columns.find(c => c.name === filter.column)?.options?.map(option => (
                    <option key={option} value={option}>{option}</option>
                  ))}
                </select>
              ) : (
                <input
                  type={columns.find(c => c.name === filter.column)?.type === 'number' ? 'number' : 
                        columns.find(c => c.name === filter.column)?.type === 'date' ? 'date' : 'text'}
                  className="form-input"
                  placeholder="Введите значение..."
                  value={filter.value}
                  onChange={(e) => updateFilter(filter.id, 'value', e.target.value)}
                />
              )}

              <button
                className="btn btn-danger"
                onClick={() => removeFilter(filter.id)}
              >
                <Trash2 className="nav-icon" style={{ width: '16px', height: '16px' }} />
              </button>
            </div>
          ))
        ) : (
          <div className="empty-state">
            <Filter className="empty-state-icon" />
            <p>Фильтры не добавлены. Нажмите "Добавить фильтр" для начала фильтрации данных.</p>
          </div>
        )}
      </div>

      {/* Sort and Limit */}
      <div className="card">
        <div className="card-header">
          <h2 className="card-title">Сортировка и лимит</h2>
        </div>
        
        <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr 1fr', gap: '1rem' }}>
          <div className="form-group">
            <label className="form-label">Сортировать по</label>
            <select
              className="form-select"
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
            >
              <option value="">Без сортировки</option>
              {columns.map(col => (
                <option key={col.name} value={col.name}>{col.name}</option>
              ))}
            </select>
          </div>

          <div className="form-group">
            <label className="form-label">Порядок</label>
            <select
              className="form-select"
              value={sortOrder}
              onChange={(e) => setSortOrder(e.target.value)}
            >
              <option value="ASC">По возрастанию</option>
              <option value="DESC">По убыванию</option>
            </select>
          </div>

          <div className="form-group">
            <label className="form-label">Лимит</label>
            <input
              type="number"
              className="form-input"
              value={limit}
              onChange={(e) => setLimit(parseInt(e.target.value))}
              min="1"
              max="10000"
            />
          </div>
        </div>
      </div>

      {/* Row Count Widget */}
      {selectedTable && (
        <div className="card" style={{ backgroundColor: '#f8fafc', border: '2px solid #e2e8f0' }}>
          <div className="card-header">
            <h2 className="card-title" style={{ color: '#3b82f6' }}>
              📊 Количество строк для выборки
            </h2>
            <button 
              className="btn btn-secondary"
              onClick={getRowCount}
              disabled={isCountLoading}
            >
              <RefreshCw className={`nav-icon ${isCountLoading ? 'animate-spin' : ''}`} style={{ width: '16px', height: '16px' }} />
              Обновить
            </button>
          </div>
          
          <div style={{ padding: '1rem' }}>
            {isCountLoading ? (
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#6b7280' }}>
                <RefreshCw className="nav-icon" style={{ width: '16px', height: '16px', animation: 'spin 1s linear infinite' }} />
                Подсчет строк...
              </div>
            ) : countError ? (
              <div style={{ color: '#dc2626', fontSize: '0.875rem' }}>
                ⚠️ {countError}
              </div>
            ) : rowCount !== null ? (
              <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                <div style={{ fontSize: '2rem', fontWeight: 'bold', color: '#059669' }}>
                  {rowCount.toLocaleString('ru-RU')}
                </div>
                <div style={{ color: '#6b7280' }}>
                  {rowCount === 1 ? 'строка' : 
                   rowCount >= 2 && rowCount <= 4 ? 'строки' : 'строк'} 
                  {filters.filter(f => f.column && f.value).length > 0 ? 
                    ' соответствует вашим фильтрам' : 
                    ' в таблице'}
                </div>
              </div>
            ) : (
              <div style={{ color: '#6b7280', fontSize: '0.875rem' }}>
                Выберите таблицу для подсчета строк
              </div>
            )}
            
            {rowCount !== null && rowCount > 1000 && (
              <div style={{ 
                marginTop: '0.5rem', 
                padding: '0.5rem', 
                backgroundColor: '#fef3cd', 
                border: '1px solid #f59e0b', 
                borderRadius: '4px',
                fontSize: '0.875rem',
                color: '#92400e'
              }}>
                💡 Большое количество строк. Рассмотрите возможность добавления фильтров для ограничения результатов.
              </div>
            )}
          </div>
        </div>
      )}

      {/* Generated SQL and Actions */}
      <div className="card">
        <div className="card-header">
          <h2 className="card-title">Сгенерированный SQL запрос</h2>
        </div>
        
        <div style={{ backgroundColor: '#f3f4f6', padding: '1rem', borderRadius: '6px', marginBottom: '1rem' }}>
          <code style={{ fontSize: '0.875rem', color: '#374151' }}>
            {generateSQL() || 'Выберите таблицу для генерации SQL запроса...'}
          </code>
        </div>

        <div className="filter-actions">
          <button 
            className="btn btn-primary"
            onClick={executeQuery}
            disabled={!selectedTable || isLoading}
          >
            {isLoading ? (
              <RefreshCw className="nav-icon" style={{ width: '16px', height: '16px', animation: 'spin 1s linear infinite' }} />
            ) : (
              <Play className="nav-icon" style={{ width: '16px', height: '16px' }} />
            )}
            {isLoading ? 'Выполняется...' : 'Выполнить запрос'}
          </button>
          
          {queryResults && (
            <button className="btn btn-success">
              <Download className="nav-icon" style={{ width: '16px', height: '16px' }} />
              Экспорт результатов
            </button>
          )}
          
          {iinInfo?.has_iin_column && (
            <button 
              className="btn btn-warning"
              onClick={openTheoryModal}
              style={{ backgroundColor: '#f59e0b', borderColor: '#f59e0b' }}
            >
              🧪 Создать теорию ({iinInfo.user_count} польз.)
            </button>
          )}
        </div>
      </div>

      {/* Query Results */}
      {queryResults && (
        <div className="card">
          <div className="card-header">
            <h2 className="card-title">Результаты запроса</h2>
            <div style={{ fontSize: '0.875rem', color: '#6b7280' }}>
              {queryResults.totalRows} строк • Время выполнения: {queryResults.executionTime}
            </div>
          </div>
          
          <div className="table-container">
            <table className="table">
              <thead>
                <tr>
                  {queryResults.columns.map(column => (
                    <th key={column}>{column}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {queryResults.data.map((row, index) => (
                  <tr key={index}>
                    {queryResults.columns.map(column => (
                      <td key={column}>{row[column]}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
      
      {/* Theory Creation Modal */}
      {showTheoryModal && (
        <div className="modal-overlay" onClick={() => setShowTheoryModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>🧪 Создание новой теории</h3>
              <button 
                className="modal-close"
                onClick={() => setShowTheoryModal(false)}
              >
                ×
              </button>
            </div>
            
            <div className="modal-body">
              <div style={{ marginBottom: '1rem', padding: '1rem', backgroundColor: '#f0f9ff', border: '1px solid #0ea5e9', borderRadius: '6px' }}>
                <div style={{ fontSize: '0.875rem', color: '#0369a1' }}>
                  📊 <strong>Найдена IIN колонка:</strong> {iinInfo?.iin_column}
                </div>
                <div style={{ fontSize: '0.875rem', color: '#0369a1', marginTop: '0.25rem' }}>
                  👥 <strong>Количество пользователей:</strong> {iinInfo?.user_count}
                </div>
              </div>
              
              <div className="form-group">
                <label className="form-label">Название теории *</label>
                <input
                  type="text"
                  className="form-input"
                  value={theoryData.theory_name}
                  onChange={(e) => setTheoryData({ ...theoryData, theory_name: e.target.value })}
                  placeholder="Введите название теории"
                />
              </div>
              
              <div className="form-group">
                <label className="form-label">Описание теории</label>
                <textarea
                  className="form-input"
                  rows="3"
                  value={theoryData.theory_description}
                  onChange={(e) => setTheoryData({ ...theoryData, theory_description: e.target.value })}
                  placeholder="Описание теории (необязательно)"
                />
              </div>
              
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <div className="form-group">
                  <label className="form-label">Дата начала *</label>
                  <input
                    type="date"
                    className="form-input"
                    value={theoryData.theory_start_date}
                    onChange={(e) => setTheoryData({ ...theoryData, theory_start_date: e.target.value })}
                  />
                </div>
                
                <div className="form-group">
                  <label className="form-label">Дата окончания *</label>
                  <input
                    type="date"
                    className="form-input"
                    value={theoryData.theory_end_date}
                    onChange={(e) => setTheoryData({ ...theoryData, theory_end_date: e.target.value })}
                  />
                </div>
              </div>
            </div>
            
            <div className="modal-footer">
              <button 
                className="btn btn-secondary"
                onClick={() => setShowTheoryModal(false)}
                disabled={isCreatingTheory}
              >
                Отмена
              </button>
              <button 
                className="btn btn-primary"
                onClick={createTheory}
                disabled={isCreatingTheory || !theoryData.theory_name}
              >
                {isCreatingTheory ? 'Создание...' : 'Создать теорию'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default QueryBuilder; 