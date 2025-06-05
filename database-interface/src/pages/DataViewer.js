import React, { useState, useEffect } from 'react';
import { 
  Search, 
  Download, 
  RefreshCw, 
  Filter,
  ChevronLeft,
  ChevronRight,
  Eye
} from 'lucide-react';
import { dataAPI, databaseAPI } from '../services/api';

const DataViewer = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [rowsPerPage, setRowsPerPage] = useState(25);
  const [sortColumn, setSortColumn] = useState('');
  const [sortDirection, setSortDirection] = useState('asc');
  const [selectedRows, setSelectedRows] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [data, setData] = useState([]);
  const [error, setError] = useState(null);
  const [selectedTable, setSelectedTable] = useState('');
  const [tables, setTables] = useState([]);
  const [columns, setColumns] = useState([]);

  // Default columns (will be updated dynamically based on table)
  const getDefaultColumns = () => [
    { key: 'id', label: 'ID', type: 'number' },
    { key: 'first_name', label: 'Имя', type: 'text' },
    { key: 'last_name', label: 'Фамилия', type: 'text' },
    { key: 'email', label: 'Email', type: 'email' },
    { key: 'department', label: 'Отдел', type: 'text' },
    { key: 'salary', label: 'Зарплата', type: 'currency' },
    { key: 'hire_date', label: 'Дата найма', type: 'date' },
    { key: 'status', label: 'Статус', type: 'badge' },
  ];

  useEffect(() => {
    loadTables();
  }, []);

  useEffect(() => {
    if (selectedTable) {
      loadTableColumns();
      loadData();
    }
  }, [selectedTable, currentPage, rowsPerPage, sortColumn, sortDirection, searchTerm]);

  const loadTables = async () => {
    try {
      const response = await databaseAPI.getDatabases();
      if (response.data && response.data.length > 0) {
        const tablesResponse = await databaseAPI.getTables(response.data[0].id);
        setTables(tablesResponse.data || []);
      }
    } catch (err) {
      console.error('Error loading tables:', err);
      setError('Ошибка загрузки таблиц');
    }
  };

  const loadTableColumns = async () => {
    try {
      const response = await databaseAPI.getTableColumns('dssb_app', selectedTable);
      const tableColumns = response.data || [];
      
      // Convert backend column format to frontend format
      const formattedColumns = tableColumns.map(col => ({
        key: col.name,
        label: col.description || col.name,
        type: mapOracleTypeToDisplayType(col.type)
      }));
      
      setColumns(formattedColumns);
    } catch (err) {
      console.error('Error loading table columns:', err);
      // Fallback to default columns
      setColumns(getDefaultColumns());
    }
  };

  const mapOracleTypeToDisplayType = (oracleType) => {
    const type = oracleType.toUpperCase();
    if (type.includes('NUMBER')) return 'number';
    if (type.includes('DATE')) return 'date';
    if (type.includes('VARCHAR')) return 'text';
    if (type.includes('CLOB')) return 'text';
    return 'text';
  };

  const loadData = async () => {
    if (!selectedTable) return;
    
    setIsLoading(true);
    setError(null);
    
    try {
      const params = {
        database_id: 'dssb_app',
        table: selectedTable,
        page: currentPage,
        limit: rowsPerPage,
        search: searchTerm,
        sort_by: sortColumn,
        sort_order: sortDirection
      };

      const response = await dataAPI.getData(params);
      setData(response.data.data || []);
      
    } catch (err) {
      console.error('Error loading data:', err);
      setError('Ошибка загрузки данных: ' + (err.response?.data?.detail || err.message));
      
      // Fallback to mock data if API fails
      setData([
        { id: 1, first_name: 'Иван', last_name: 'Петров', email: 'ivan@example.com', department: 'Продажи', salary: 75000, hire_date: '2020-01-15', status: 'active' },
        { id: 2, first_name: 'Мария', last_name: 'Смирнова', email: 'maria@example.com', department: 'Маркетинг', salary: 68000, hire_date: '2019-03-20', status: 'active' },
        { id: 3, first_name: 'Алексей', last_name: 'Иванов', email: 'alex@example.com', department: 'ИТ', salary: 82000, hire_date: '2021-07-10', status: 'active' },
        { id: 4, first_name: 'Анна', last_name: 'Козлова', email: 'anna@example.com', department: 'HR', salary: 62000, hire_date: '2018-11-05', status: 'inactive' },
        { id: 5, first_name: 'Сергей', last_name: 'Волков', email: 'sergey@example.com', department: 'Финансы', salary: 78000, hire_date: '2020-09-12', status: 'active' },
        { id: 6, first_name: 'Елена', last_name: 'Павлова', email: 'elena@example.com', department: 'Продажи', salary: 71000, hire_date: '2019-12-03', status: 'active' },
        { id: 7, first_name: 'Дмитрий', last_name: 'Соколов', email: 'dmitry@example.com', department: 'ИТ', salary: 85000, hire_date: '2021-02-18', status: 'active' },
        { id: 8, first_name: 'Ольга', last_name: 'Морозова', email: 'olga@example.com', department: 'Маркетинг', salary: 64000, hire_date: '2020-06-25', status: 'inactive' },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  // Filter data based on search term
  const filteredData = data.filter(row =>
    Object.values(row).some(value =>
      value.toString().toLowerCase().includes(searchTerm.toLowerCase())
    )
  );

  // Sort data
  const sortedData = [...filteredData].sort((a, b) => {
    if (!sortColumn) return 0;
    
    let aVal = a[sortColumn];
    let bVal = b[sortColumn];
    
    // Handle different data types
    if (typeof aVal === 'string') {
      aVal = aVal.toLowerCase();
      bVal = bVal.toLowerCase();
    }
    
    if (aVal < bVal) return sortDirection === 'asc' ? -1 : 1;
    if (aVal > bVal) return sortDirection === 'asc' ? 1 : -1;
    return 0;
  });

  // Paginate data
  const totalPages = Math.ceil(sortedData.length / rowsPerPage);
  const startIndex = (currentPage - 1) * rowsPerPage;
  const paginatedData = sortedData.slice(startIndex, startIndex + rowsPerPage);

  const handleSort = (column) => {
    if (sortColumn === column) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortColumn(column);
      setSortDirection('asc');
    }
  };

  const handleRowSelect = (id) => {
    setSelectedRows(prev =>
      prev.includes(id)
        ? prev.filter(rowId => rowId !== id)
        : [...prev, id]
    );
  };

  const handleSelectAll = () => {
    if (selectedRows.length === paginatedData.length) {
      setSelectedRows([]);
    } else {
      setSelectedRows(paginatedData.map(row => row.id));
    }
  };

  const formatCellValue = (value, type) => {
    switch (type) {
      case 'currency':
        return new Intl.NumberFormat('ru-RU', {
          style: 'currency',
          currency: 'RUB'
        }).format(value);
      case 'date':
        return new Date(value).toLocaleDateString('ru-RU');
      case 'badge':
        return (
          <span className={`badge ${value === 'active' ? 'badge-success' : 'badge-warning'}`}>
            {value === 'active' ? 'Активный' : 'Неактивный'}
          </span>
        );
      default:
        return value;
    }
  };

  const refreshData = async () => {
    await loadData();
  };

  const exportData = async () => {
    try {
      const response = await dataAPI.exportData({
        database_id: 'dssb_app',
        table: selectedTable,
        search: searchTerm,
        sort_by: sortColumn,
        sort_order: sortDirection
      });
      
      const url = window.URL.createObjectURL(response.data);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${selectedTable}_export.csv`;
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Export error:', err);
      // Fallback to client-side export
      const csvContent = [
        columns.map(col => col.label).join(','),
        ...sortedData.map(row =>
          columns.map(col => row[col.key]).join(',')
        )
      ].join('\n');

      const blob = new Blob([csvContent], { type: 'text/csv' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'export-data.csv';
      a.click();
      window.URL.revokeObjectURL(url);
    }
  };

  return (
    <div className="data-viewer">
      <div className="dashboard-header">
        <h1 className="dashboard-title">Просмотр данных</h1>
        <p className="dashboard-subtitle">
          Просматривайте и анализируйте записи вашей базы данных
        </p>
      </div>

      {error && (
        <div className="alert alert-error" style={{ marginBottom: '1.5rem' }}>
          {error}
        </div>
      )}

      {/* Table Selection */}
      <div className="card" style={{ marginBottom: '1.5rem' }}>
        <div className="card-header">
          <h2 className="card-title">Выбор таблицы</h2>
        </div>
        <div className="form-group">
          <select 
            className="form-select"
            value={selectedTable}
            onChange={(e) => {
              setSelectedTable(e.target.value);
              setCurrentPage(1);
              setSelectedRows([]);
            }}
          >
            <option value="">Выберите таблицу для просмотра...</option>
            {tables.map(table => (
              <option key={table.name} value={table.name}>
                {table.name} - {table.description}
              </option>
            ))}
          </select>
        </div>
      </div>

      {selectedTable && (
        <>
          {/* Controls */}
          <div className="card">
            <div className="card-header">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', flex: 1 }}>
                  <div style={{ position: 'relative', minWidth: '300px' }}>
                    <Search 
                      className="search-icon" 
                      style={{ 
                        position: 'absolute', 
                        left: '0.75rem', 
                        top: '50%', 
                        transform: 'translateY(-50%)', 
                        width: '16px', 
                        height: '16px', 
                        color: '#6b7280' 
                      }} 
                    />
                    <input
                      type="text"
                      placeholder="Поиск по всем столбцам..."
                      className="form-input"
                      style={{ paddingLeft: '2.5rem' }}
                      value={searchTerm}
                      onChange={(e) => setSearchTerm(e.target.value)}
                    />
                  </div>
                  
                  <select
                    className="form-select"
                    value={rowsPerPage}
                    onChange={(e) => {
                      setRowsPerPage(parseInt(e.target.value));
                      setCurrentPage(1);
                    }}
                    style={{ width: 'auto' }}
                  >
                    <option value={10}>10 строк</option>
                    <option value={25}>25 строк</option>
                    <option value={50}>50 строк</option>
                    <option value={100}>100 строк</option>
                  </select>
                </div>

                <div style={{ display: 'flex', gap: '0.5rem' }}>
                  <button 
                    className="btn btn-secondary"
                    onClick={refreshData}
                    disabled={isLoading}
                  >
                    <RefreshCw 
                      className="nav-icon" 
                      style={{ 
                        width: '16px', 
                        height: '16px',
                        animation: isLoading ? 'spin 1s linear infinite' : 'none'
                      }} 
                    />
                    Обновить
                  </button>
                  
                  <button 
                    className="btn btn-success"
                    onClick={exportData}
                    disabled={!selectedTable}
                  >
                    <Download className="nav-icon" style={{ width: '16px', height: '16px' }} />
                    Экспорт
                  </button>
                </div>
              </div>
            </div>

            {/* Statistics */}
            <div style={{ 
              display: 'flex', 
              justifyContent: 'space-between', 
              alignItems: 'center', 
              padding: '1rem', 
              backgroundColor: '#f9fafb', 
              borderRadius: '6px',
              fontSize: '0.875rem',
              color: '#6b7280'
            }}>
              <div>
                Показано {startIndex + 1} до {Math.min(startIndex + rowsPerPage, sortedData.length)} из {sortedData.length} записей
                {searchTerm && ` (отфильтровано из ${data.length} всего)`}
              </div>
              {selectedRows.length > 0 && (
                <div>
                  {selectedRows.length} {selectedRows.length === 1 ? 'строка выбрана' : selectedRows.length < 5 ? 'строки выбрано' : 'строк выбрано'}
                </div>
              )}
            </div>
          </div>

          {/* Data Table */}
          <div className="table-container">
            <table className="table">
              <thead>
                <tr>
                  <th style={{ width: '50px' }}>
                    <input
                      type="checkbox"
                      checked={selectedRows.length === paginatedData.length && paginatedData.length > 0}
                      onChange={handleSelectAll}
                    />
                  </th>
                  {columns.map((column) => (
                    <th
                      key={column.key}
                      style={{ cursor: 'pointer', userSelect: 'none' }}
                      onClick={() => handleSort(column.key)}
                    >
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        {column.label}
                        {sortColumn === column.key && (
                          <span style={{ fontSize: '0.75rem' }}>
                            {sortDirection === 'asc' ? '↑' : '↓'}
                          </span>
                        )}
                      </div>
                    </th>
                  ))}
                  <th style={{ width: '100px' }}>Действия</th>
                </tr>
              </thead>
              <tbody>
                {paginatedData.length > 0 ? (
                  paginatedData.map((row) => (
                    <tr key={row.id}>
                      <td>
                        <input
                          type="checkbox"
                          checked={selectedRows.includes(row.id)}
                          onChange={() => handleRowSelect(row.id)}
                        />
                      </td>
                      {columns.map((column) => (
                        <td key={column.key}>
                          {formatCellValue(row[column.key], column.type)}
                        </td>
                      ))}
                      <td>
                        <button
                          className="btn btn-secondary"
                          style={{ padding: '0.25rem 0.5rem', fontSize: '0.75rem' }}
                        >
                          <Eye style={{ width: '14px', height: '14px' }} />
                        </button>
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={columns.length + 2} className="empty-state">
                      <Filter className="empty-state-icon" />
                      <p>Данные, соответствующие критериям поиска, не найдены</p>
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="card">
              <div style={{ 
                display: 'flex', 
                justifyContent: 'space-between', 
                alignItems: 'center', 
                padding: '1rem' 
              }}>
                <div style={{ fontSize: '0.875rem', color: '#6b7280' }}>
                  Страница {currentPage} из {totalPages}
                </div>
                
                <div style={{ display: 'flex', gap: '0.5rem' }}>
                  <button
                    className="btn btn-secondary"
                    onClick={() => setCurrentPage(prev => Math.max(prev - 1, 1))}
                    disabled={currentPage === 1}
                  >
                    <ChevronLeft style={{ width: '16px', height: '16px' }} />
                    Назад
                  </button>
                  
                  {/* Page numbers */}
                  {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                    let pageNum;
                    if (totalPages <= 5) {
                      pageNum = i + 1;
                    } else if (currentPage <= 3) {
                      pageNum = i + 1;
                    } else if (currentPage >= totalPages - 2) {
                      pageNum = totalPages - 4 + i;
                    } else {
                      pageNum = currentPage - 2 + i;
                    }
                    
                    return (
                      <button
                        key={pageNum}
                        className={`btn ${currentPage === pageNum ? 'btn-primary' : 'btn-secondary'}`}
                        onClick={() => setCurrentPage(pageNum)}
                        style={{ minWidth: '40px' }}
                      >
                        {pageNum}
                      </button>
                    );
                  })}
                  
                  <button
                    className="btn btn-secondary"
                    onClick={() => setCurrentPage(prev => Math.min(prev + 1, totalPages))}
                    disabled={currentPage === totalPages}
                  >
                    Вперед
                    <ChevronRight style={{ width: '16px', height: '16px' }} />
                  </button>
                </div>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default DataViewer; 