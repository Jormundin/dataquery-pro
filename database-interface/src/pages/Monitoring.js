import React, { useState, useEffect } from 'react';
import { 
  Activity, 
  Database, 
  Users, 
  TrendingUp,
  Calendar,
  BarChart3,
  FileText,
  Clock,
  Target,
  Shield,
  RefreshCw,
  AlertCircle
} from 'lucide-react';
import { databaseAPI } from '../services/api';

const Monitoring = () => {
  const [overview, setOverview] = useState(null);
  const [dailyStats, setDailyStats] = useState(null);
  const [campaignDistribution, setCampaignDistribution] = useState(null);
  const [recentActivity, setRecentActivity] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedDays, setSelectedDays] = useState(7);
  const [lastUpdated, setLastUpdated] = useState(new Date());

  useEffect(() => {
    loadMonitoringData();
  }, [selectedDays]);

  const loadMonitoringData = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      // Load all monitoring data in parallel
      const [overviewResponse, dailyResponse, distributionResponse, activityResponse] = await Promise.all([
        databaseAPI.get('/monitoring/overview'),
        databaseAPI.get(`/monitoring/daily-statistics?days_back=${selectedDays}`),
        databaseAPI.get('/monitoring/campaign-distribution'),
        databaseAPI.get('/monitoring/recent-activity?limit=50')
      ]);

      setOverview(overviewResponse.data.overview);
      setDailyStats(dailyResponse.data.daily_statistics);
      setCampaignDistribution(distributionResponse.data.campaign_distribution);
      setRecentActivity(activityResponse.data.recent_activity);
      setLastUpdated(new Date());
      
    } catch (err) {
      console.error('Error loading monitoring data:', err);
      setError('Ошибка загрузки данных мониторинга. Проверьте соединение с сервером.');
    } finally {
      setIsLoading(false);
    }
  };

  const formatNumber = (num) => {
    if (num === null || num === undefined) return 'Н/Д';
    return num.toLocaleString();
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return 'Н/Д';
    try {
      return new Date(dateStr).toLocaleDateString('ru-RU');
    } catch {
      return dateStr;
    }
  };

  const formatDateTime = (dateStr) => {
    if (!dateStr) return 'Н/Д';
    try {
      return new Date(dateStr).toLocaleString('ru-RU');
    } catch {
      return dateStr;
    }
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case 'Active':
        return <span className="badge badge-success">Активная</span>;
      case 'Inactive':
        return <span className="badge badge-secondary">Неактивная</span>;
      default:
        return <span className="badge badge-secondary">{status}</span>;
    }
  };

  const getActivityTypeIcon = (activityType) => {
    switch (activityType) {
      case 'Control Group':
        return <Shield size={16} className="text-blue-500" />;
      case 'Target Group':
        return <Target size={16} className="text-green-500" />;
      case 'SPSS Target':
        return <Database size={16} className="text-purple-500" />;
      default:
        return <Activity size={16} className="text-gray-500" />;
    }
  };

  if (isLoading) {
    return (
      <div className="monitoring">
        <div className="dashboard-header">
          <h1 className="dashboard-title">Мониторинг системы</h1>
          <p className="dashboard-subtitle">Загрузка данных мониторинга...</p>
        </div>
        <div style={{ textAlign: 'center', padding: '3rem' }}>
          <div className="loading-spinner"></div>
          <p>Загрузка статистики...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="monitoring">
      <div className="dashboard-header">
        <div>
          <h1 className="dashboard-title">Мониторинг системы</h1>
          <p className="dashboard-subtitle">
            Статистика загрузок и распределения пользователей по кампаниям
          </p>
          <small style={{ color: '#6b7280' }}>
            Последнее обновление: {lastUpdated.toLocaleString('ru-RU')}
          </small>
        </div>
        <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
          <select 
            value={selectedDays} 
            onChange={(e) => setSelectedDays(parseInt(e.target.value))}
            className="form-control"
            style={{ width: 'auto' }}
          >
            <option value={7}>За 7 дней</option>
            <option value={14}>За 14 дней</option>
            <option value={30}>За 30 дней</option>
          </select>
          <button className="btn btn-primary" onClick={loadMonitoringData}>
            <RefreshCw size={16} />
            Обновить
          </button>
        </div>
      </div>

      {error && (
        <div className="alert alert-error" style={{ marginBottom: '1.5rem' }}>
          <AlertCircle size={20} />
          {error}
        </div>
      )}

      {/* Overview Statistics */}
      {overview && (
        <>
          <div className="card" style={{ marginBottom: '1.5rem' }}>
            <div className="card-header">
              <h2 className="card-title">Обзор таблиц</h2>
            </div>
            <div className="stats-grid">
              <div className="stat-card">
                <div className="stat-icon">
                  <Shield className="nav-icon" style={{ color: '#3b82f6' }} />
                </div>
                <div className="stat-content">
                  <div className="stat-number">
                    {formatNumber(overview.tables.sc_local_control?.total_users)}
                  </div>
                  <div className="stat-label">Контрольная группа</div>
                  <div className="stat-sublabel">
                    {formatNumber(overview.tables.sc_local_control?.unique_campaigns)} кампаний
                  </div>
                </div>
              </div>

              <div className="stat-card">
                <div className="stat-icon">
                  <Target className="nav-icon" style={{ color: '#10b981' }} />
                </div>
                <div className="stat-content">
                  <div className="stat-number">
                    {formatNumber(overview.tables.sc_local_target?.total_users)}
                  </div>
                  <div className="stat-label">Целевые группы</div>
                  <div className="stat-sublabel">
                    {formatNumber(overview.tables.sc_local_target?.unique_campaigns)} кампаний
                  </div>
                </div>
              </div>

              <div className="stat-card">
                <div className="stat-icon">
                  <Database className="nav-icon" style={{ color: '#8b5cf6' }} />
                </div>
                <div className="stat-content">
                  <div className="stat-number">
                    {overview.tables.spss_sc_theory_users?.error 
                      ? 'Ошибка' 
                      : formatNumber(overview.tables.spss_sc_theory_users?.total_users)
                    }
                  </div>
                  <div className="stat-label">SPSS пользователи</div>
                  <div className="stat-sublabel">
                    {overview.tables.spss_sc_theory_users?.error 
                      ? 'Нет подключения' 
                      : `${formatNumber(overview.tables.spss_sc_theory_users?.unique_campaigns)} кампаний`
                    }
                  </div>
                </div>
              </div>

              <div className="stat-card">
                <div className="stat-icon">
                  <FileText className="nav-icon" style={{ color: '#f59e0b' }} />
                </div>
                <div className="stat-content">
                  <div className="stat-number">
                    {formatNumber(overview.campaigns?.total_campaigns)}
                  </div>
                  <div className="stat-label">Всего кампаний</div>
                  <div className="stat-sublabel">
                    {formatNumber(overview.campaigns?.active_campaigns)} активных
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Daily Statistics */}
          {dailyStats && (
            <div className="card" style={{ marginBottom: '1.5rem' }}>
              <div className="card-header">
                <h2 className="card-title">
                  <BarChart3 size={20} />
                  Ежедневная статистика загрузок ({dailyStats.period})
                </h2>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr 1fr', gap: '1rem', marginBottom: '1.5rem' }}>
                <div className="stat-card-small">
                  <div className="stat-content">
                    <div className="stat-number" style={{ color: '#3b82f6' }}>
                      {formatNumber(dailyStats.summary?.total_control_uploads)}
                    </div>
                    <div className="stat-label">Контроль</div>
                  </div>
                </div>
                <div className="stat-card-small">
                  <div className="stat-content">
                    <div className="stat-number" style={{ color: '#10b981' }}>
                      {formatNumber(dailyStats.summary?.total_target_uploads)}
                    </div>
                    <div className="stat-label">Целевые</div>
                  </div>
                </div>
                <div className="stat-card-small">
                  <div className="stat-content">
                    <div className="stat-number" style={{ color: '#8b5cf6' }}>
                      {formatNumber(dailyStats.summary?.total_spss_uploads)}
                    </div>
                    <div className="stat-label">SPSS</div>
                  </div>
                </div>
                <div className="stat-card-small">
                  <div className="stat-content">
                    <div className="stat-number" style={{ color: '#f59e0b' }}>
                      {formatNumber(dailyStats.summary?.total_uploads)}
                    </div>
                    <div className="stat-label">Всего</div>
                  </div>
                </div>
              </div>

              <div className="table-container">
                <table className="table">
                  <thead>
                    <tr>
                      <th>Дата</th>
                      <th>Контроль</th>
                      <th>Целевые</th>
                      <th>SPSS</th>
                      <th>Всего</th>
                    </tr>
                  </thead>
                  <tbody>
                    {dailyStats.sc_local_control.map((controlDay, index) => {
                      const targetDay = dailyStats.sc_local_target.find(t => t.upload_date === controlDay.upload_date) || {};
                      const spssDay = dailyStats.spss_sc_theory_users.find(s => s.upload_date === controlDay.upload_date) || {};
                      const total = (controlDay.users_uploaded || 0) + (targetDay.users_uploaded || 0) + (spssDay.users_uploaded || 0);
                      
                      return (
                        <tr key={controlDay.upload_date}>
                          <td>{formatDate(controlDay.upload_date)}</td>
                          <td style={{ color: '#3b82f6' }}>{formatNumber(controlDay.users_uploaded)}</td>
                          <td style={{ color: '#10b981' }}>{formatNumber(targetDay.users_uploaded)}</td>
                          <td style={{ color: '#8b5cf6' }}>{formatNumber(spssDay.users_uploaded)}</td>
                          <td style={{ fontWeight: 'bold' }}>{formatNumber(total)}</td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>
        {/* Campaign Distribution */}
        {campaignDistribution && (
          <div className="card">
            <div className="card-header">
              <h2 className="card-title">
                <TrendingUp size={20} />
                Распределение по кампаниям
              </h2>
              <div style={{ fontSize: '0.875rem', color: '#6b7280' }}>
                Всего: {formatNumber(campaignDistribution.totals?.total_actual_users)} пользователей
              </div>
            </div>
            <div className="table-container" style={{ maxHeight: '500px' }}>
              <table className="table">
                <thead>
                  <tr>
                    <th>Кампания</th>
                    <th>Статус</th>
                    <th>Контроль</th>
                    <th>Целевые</th>
                    <th>SPSS</th>
                    <th>Всего</th>
                  </tr>
                </thead>
                <tbody>
                  {campaignDistribution.campaigns?.slice(0, 20).map((campaign) => (
                    <tr key={campaign.theory_id}>
                      <td>
                        <div title={campaign.theory_name}>
                          <strong>{campaign.theory_id}</strong>
                          <div style={{ fontSize: '0.75rem', color: '#6b7280' }}>
                            {campaign.theory_name?.length > 30 
                              ? `${campaign.theory_name.substring(0, 30)}...`
                              : campaign.theory_name
                            }
                          </div>
                        </div>
                      </td>
                      <td>{getStatusBadge(campaign.status)}</td>
                      <td style={{ color: '#3b82f6' }}>{formatNumber(campaign.control_users)}</td>
                      <td style={{ color: '#10b981' }}>{formatNumber(campaign.target_users)}</td>
                      <td style={{ color: '#8b5cf6' }}>
                        {typeof campaign.spss_users === 'string' && campaign.spss_users.includes('Error') 
                          ? 'Ошибка' 
                          : formatNumber(campaign.spss_users)
                        }
                      </td>
                      <td style={{ fontWeight: 'bold' }}>{formatNumber(campaign.total_actual_users)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Recent Activity */}
        {recentActivity && (
          <div className="card">
            <div className="card-header">
              <h2 className="card-title">
                <Activity size={20} />
                Последняя активность
              </h2>
              <div style={{ fontSize: '0.875rem', color: '#6b7280' }}>
                {recentActivity.summary?.period} • {formatNumber(recentActivity.summary?.total_users_uploaded)} пользователей
              </div>
            </div>
            <div className="table-container" style={{ maxHeight: '500px' }}>
              <table className="table">
                <thead>
                  <tr>
                    <th>Тип</th>
                    <th>Кампания</th>
                    <th>Пользователи</th>
                    <th>Время</th>
                    <th>Доп. поля</th>
                  </tr>
                </thead>
                <tbody>
                  {recentActivity.activities?.map((activity, index) => (
                    <tr key={index}>
                      <td>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                          {getActivityTypeIcon(activity.activity_type)}
                          <span style={{ fontSize: '0.75rem' }}>
                            {activity.activity_type}
                          </span>
                        </div>
                      </td>
                      <td>
                        <code style={{ fontSize: '0.75rem' }}>{activity.theory_id}</code>
                      </td>
                      <td>{formatNumber(activity.users_count)}</td>
                      <td style={{ fontSize: '0.75rem' }}>
                        {formatDateTime(activity.upload_time)}
                      </td>
                      <td style={{ fontSize: '0.75rem', color: '#6b7280' }}>
                        {activity.tab1 && (
                          <div title={`tab1: ${activity.tab1}, tab2: ${activity.tab2}`}>
                            {activity.tab1?.length > 15 
                              ? `${activity.tab1.substring(0, 15)}...`
                              : activity.tab1
                            }
                          </div>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>

      {/* Summary Cards */}
      {campaignDistribution && (
        <div className="card" style={{ marginTop: '1.5rem' }}>
          <div className="card-header">
            <h2 className="card-title">Сводная статистика</h2>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem' }}>
            <div className="summary-stat">
              <div className="summary-label">Всего кампаний</div>
              <div className="summary-value">{formatNumber(campaignDistribution.totals?.total_campaigns)}</div>
            </div>
            <div className="summary-stat">
              <div className="summary-label">Активных кампаний</div>
              <div className="summary-value" style={{ color: '#10b981' }}>
                {formatNumber(campaignDistribution.totals?.active_campaigns)}
              </div>
            </div>
            <div className="summary-stat">
              <div className="summary-label">Планируемых пользователей</div>
              <div className="summary-value">{formatNumber(campaignDistribution.totals?.total_planned_users)}</div>
            </div>
            <div className="summary-stat">
              <div className="summary-label">Фактических пользователей</div>
              <div className="summary-value" style={{ color: '#3b82f6' }}>
                {formatNumber(campaignDistribution.totals?.total_actual_users)}
              </div>
            </div>
            <div className="summary-stat">
              <div className="summary-label">Контрольная группа</div>
              <div className="summary-value" style={{ color: '#f59e0b' }}>
                {formatNumber(campaignDistribution.totals?.total_control_users)}
              </div>
            </div>
            <div className="summary-stat">
              <div className="summary-label">Целевые группы</div>
              <div className="summary-value" style={{ color: '#8b5cf6' }}>
                {formatNumber(campaignDistribution.totals?.total_target_users)}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Monitoring; 