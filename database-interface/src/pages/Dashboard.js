import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { 
  Database, 
  Search, 
  BarChart3, 
  Users, 
  Activity,
  TrendingUp,
  Clock
} from 'lucide-react';
import { databaseAPI, dataAPI } from '../services/api';

const Dashboard = () => {
  const [stats, setStats] = useState({
    totalQueries: 0,
    activeDatabases: 0,
    totalUsers: 0,
    avgResponseTime: '0s'
  });
  const [recentQueries, setRecentQueries] = useState([]);
  const [databases, setDatabases] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      // Load databases - backend returns direct array
      const dbResponse = await databaseAPI.getDatabases();
      setDatabases(dbResponse.data || []); // Changed: removed .databases
      
      // Load query history - backend returns direct array  
      const historyResponse = await databaseAPI.getQueryHistory(1, 4);
      setRecentQueries(historyResponse.data || []); // Changed: removed .queries
      
      // Update stats based on loaded data
      setStats({
        totalQueries: historyResponse.data ? historyResponse.data.length : 0, // Updated
        activeDatabases: dbResponse.data ? dbResponse.data.length : 0, // Updated
        totalUsers: 156, // This would come from user management API
        avgResponseTime: '0.8s' // This would come from performance metrics API
      });
      
    } catch (err) {
      console.error('Error loading dashboard data:', err);
      setError('Ошибка загрузки данных. Проверьте соединение с сервером.');
      
      // Fallback to mock data if API fails
      setStats({
        totalQueries: 1247,
        activeDatabases: 8,
        totalUsers: 156,
        avgResponseTime: '0.8s'
      });
      
      setRecentQueries([
        { id: 1, query: 'Анализ клиентских данных', table: 'customers', time: '2 минуты назад', status: 'success' },
        { id: 2, query: 'Отчет по продажам за 4 квартал', table: 'sales', time: '5 минут назад', status: 'success' },
        { id: 3, query: 'Аудит прав пользователей', table: 'users', time: '12 минут назад', status: 'pending' },
        { id: 4, query: 'Проверка уровня запасов', table: 'inventory', time: '18 минут назад', status: 'success' },
      ]);
      
      setDatabases([
        { name: 'Продуктивная БД', status: 'active', tables: 24, lastAccess: '2 мин назад' },
        { name: 'Аналитическая БД', status: 'active', tables: 12, lastAccess: '5 мин назад' },
        { name: 'Управление пользователями', status: 'active', tables: 8, lastAccess: '1 час назад' },
        { name: 'БД логов', status: 'maintenance', tables: 6, lastAccess: '3 часа назад' },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const testConnection = async () => {
    try {
      await databaseAPI.testConnection({});
      alert('Соединение успешно!');
    } catch (err) {
      alert('Ошибка соединения: ' + (err.response?.data?.detail || err.message));
    }
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case 'success':
        return <span className="badge badge-success">Выполнено</span>;
      case 'pending':
        return <span className="badge badge-warning">В процессе</span>;
      case 'error':
        return <span className="badge badge-error">Ошибка</span>;
      case 'active':
        return <span className="badge badge-success">Активна</span>;
      case 'maintenance':
        return <span className="badge badge-warning">Обслуживание</span>;
      default:
        return <span className="badge badge-secondary">{status}</span>;
    }
  };

  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <h1 className="dashboard-title">Панель управления</h1>
        <p className="dashboard-subtitle">
          Обзор активности базы данных и статистика запросов
        </p>
      </div>

      {error && (
        <div className="alert alert-error" style={{ marginBottom: '1.5rem' }}>
          {error}
        </div>
      )}

      {isLoading ? (
        <div style={{ textAlign: 'center', padding: '2rem' }}>
          <div className="loading-spinner"></div>
          <p>Загрузка данных...</p>
        </div>
      ) : (
        <>
          {/* Statistics Cards */}
          <div className="stats-grid">
            <div className="stat-card">
              <div className="stat-icon">
                <Search className="nav-icon" />
              </div>
              <div className="stat-content">
                <div className="stat-number">{stats.totalQueries.toLocaleString()}</div>
                <div className="stat-label">Всего запросов</div>
              </div>
            </div>

            <div className="stat-card">
              <div className="stat-icon">
                <Database className="nav-icon" />
              </div>
              <div className="stat-content">
                <div className="stat-number">{stats.activeDatabases}</div>
                <div className="stat-label">Активных БД</div>
              </div>
            </div>

            <div className="stat-card">
              <div className="stat-icon">
                <Users className="nav-icon" />
              </div>
              <div className="stat-content">
                <div className="stat-number">{stats.totalUsers}</div>
                <div className="stat-label">Пользователей</div>
              </div>
            </div>

            <div className="stat-card">
              <div className="stat-icon">
                <Clock className="nav-icon" />
              </div>
              <div className="stat-content">
                <div className="stat-number">{stats.avgResponseTime}</div>
                <div className="stat-label">Среднее время ответа</div>
              </div>
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '1.5rem' }}>
            {/* Recent Queries */}
            <div className="card">
              <div className="card-header">
                <h2 className="card-title">Последние запросы</h2>
              </div>
              <div className="table-container">
                <table className="table">
                  <thead>
                    <tr>
                      <th>Запрос</th>
                      <th>Таблица</th>
                      <th>Время</th>
                      <th>Статус</th>
                    </tr>
                  </thead>
                  <tbody>
                    {recentQueries.length > 0 ? (
                      recentQueries.map((query) => (
                        <tr key={query.id}>
                          <td>{query.query}</td>
                          <td><code>{query.table}</code></td>
                          <td>{query.time}</td>
                          <td>{getStatusBadge(query.status)}</td>
                        </tr>
                      ))
                    ) : (
                      <tr>
                        <td colSpan="4" style={{ textAlign: 'center', color: '#6b7280' }}>
                          Нет данных о запросах
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Database Status */}
            <div className="card">
              <div className="card-header">
                <h2 className="card-title">Статус баз данных</h2>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                {databases.length > 0 ? (
                  databases.map((db, index) => (
                    <div key={index} className="database-status-item">
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                        <span style={{ fontWeight: '500' }}>{db.name}</span>
                        {getStatusBadge(db.status)}
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.875rem', color: '#6b7280' }}>
                        <span>{db.tables} таблиц</span>
                        <span>Доступ: {db.lastAccess}</span>
                      </div>
                    </div>
                  ))
                ) : (
                  <div style={{ textAlign: 'center', color: '#6b7280', padding: '1rem' }}>
                    Нет доступных баз данных
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Quick Actions */}
          <div className="card">
            <div className="card-header">
              <h2 className="card-title">Быстрые действия</h2>
            </div>
            <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
              <Link to="/query-builder" className="btn btn-primary">
                <Search className="nav-icon" style={{ width: '16px', height: '16px' }} />
                Создать новый запрос
              </Link>
              <Link to="/data-viewer" className="btn btn-secondary">
                <BarChart3 className="nav-icon" style={{ width: '16px', height: '16px' }} />
                Просмотр данных
              </Link>
              <button className="btn btn-success" onClick={testConnection}>
                <Database className="nav-icon" style={{ width: '16px', height: '16px' }} />
                Тест соединения
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default Dashboard; 