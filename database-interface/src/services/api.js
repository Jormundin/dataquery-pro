import axios from 'axios';

// Create axios instance with default configuration
const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8000',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth tokens
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('authToken');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for error handling and token refresh
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Handle unauthorized access - clear token and redirect to login
      localStorage.removeItem('authToken');
      localStorage.removeItem('userInfo');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Authentication API endpoints
export const authAPI = {
  // Login with LDAP credentials
  login: (credentials) => api.post('/auth/login', credentials),
  
  // Get current user info
  getCurrentUser: () => api.get('/auth/me'),
  
  // Logout
  logout: () => {
    localStorage.removeItem('authToken');
    localStorage.removeItem('userInfo');
    return api.post('/auth/logout');
  },
  
  // Check if user is authenticated
  isAuthenticated: () => {
    const token = localStorage.getItem('authToken');
    const userInfo = localStorage.getItem('userInfo');
    return !!(token && userInfo);
  },
  
  // Get stored user info
  getUserInfo: () => {
    const userInfo = localStorage.getItem('userInfo');
    return userInfo ? JSON.parse(userInfo) : null;
  }
};

// Database API endpoints
export const databaseAPI = {
  // Authentication
  login: authAPI.login,
  logout: authAPI.logout,
  getCurrentUser: authAPI.getCurrentUser,
  
  // Get all databases
  getDatabases: () => api.get('/databases'),
  
  // Get tables for a specific database
  getTables: (databaseId) => api.get(`/databases/${databaseId}/tables`),
  
  // Get columns for a specific table
  getTableColumns: (databaseId, tableName) => 
    api.get(`/databases/${databaseId}/tables/${tableName}/columns`),
  
  // Test database connection
  testConnection: (connectionData) => 
    api.post('/databases/test-connection', connectionData),
  
  // Execute query
  executeQuery: (queryData) => 
    api.post('/query/execute', queryData),
  
  // Get query history
  getQueryHistory: (page = 1, limit = 10) => 
    api.get(`/query/history?page=${page}&limit=${limit}`),
  
  // Save query
  saveQuery: (queryData) => 
    api.post('/query/save', queryData),
  
  // Get saved queries
  getSavedQueries: () => 
    api.get('/query/saved'),
  
  // Delete saved query
  deleteSavedQuery: (queryId) => 
    api.delete(`/query/saved/${queryId}`),
  
  // Get row count
  getRowCount: (queryData) => 
    api.post('/query/count', queryData),
  
  // Get dashboard statistics
  getStats: () => 
    api.get('/stats'),
  
  // Theory Management
  createTheory: (theoryData) => 
    api.post('/theories/create', theoryData),
  
  getActiveTheories: () => 
    api.get('/theories/active'),
  
  detectIINs: (resultsData) => 
    api.post('/theories/detect-iins', resultsData),
};

// Data API endpoints
export const dataAPI = {
  // Get data with filters and pagination
  getData: (params) => api.get('/data', { params }),
  
  // Export data
  exportData: (params) => 
    api.get('/data/export', { 
      params, 
      responseType: 'blob'
    }),
  
  // Get data statistics
  getDataStats: (tableName) => 
    api.get(`/data/stats/${tableName}`),
};

// Settings API endpoints
export const settingsAPI = {
  // Get user settings
  getSettings: () => api.get('/settings'),
  
  // Update user settings
  updateSettings: (settings) => 
    api.put('/settings', settings),
  
  // Get database configuration
  getDatabaseConfig: () => 
    api.get('/settings/database'),
  
  // Update database configuration
  updateDatabaseConfig: (config) => 
    api.put('/settings/database', config),
};

// Query builder helpers
export const queryBuilder = {
  // Build SQL query from visual query builder data
  buildQuery: (queryData) => {
    const { table, columns, filters, sortBy, sortOrder, limit } = queryData;
    
    let sql = 'SELECT ';
    
    // Add columns
    if (columns && columns.length > 0) {
      sql += columns.join(', ');
    } else {
      sql += '*';
    }
    
    sql += ` FROM ${table}`;
    
    // Add WHERE clause
    if (filters && filters.length > 0) {
      const conditions = filters
        .filter(f => f.column && f.value)
        .map(f => {
          let value = f.value;
          
          // Handle string values
          if (typeof value === 'string' && f.operator !== 'IS NULL' && f.operator !== 'IS NOT NULL') {
            if (f.operator === 'LIKE' || f.operator === 'NOT LIKE') {
              value = `'%${value}%'`;
            } else {
              value = `'${value}'`;
            }
          }
          
          switch (f.operator) {
            case 'equals':
              return `${f.column} = ${value}`;
            case 'not_equals':
              return `${f.column} != ${value}`;
            case 'contains':
              return `${f.column} LIKE ${value}`;
            case 'not_contains':
              return `${f.column} NOT LIKE ${value}`;
            case 'greater_than':
              return `${f.column} > ${value}`;
            case 'less_than':
              return `${f.column} < ${value}`;
            case 'greater_equal':
              return `${f.column} >= ${value}`;
            case 'less_equal':
              return `${f.column} <= ${value}`;
            case 'is_null':
              return `${f.column} IS NULL`;
            case 'is_not_null':
              return `${f.column} IS NOT NULL`;
            case 'in':
              return `${f.column} IN (${value})`;
            case 'not_in':
              return `${f.column} NOT IN (${value})`;
            default:
              return `${f.column} = ${value}`;
          }
        });
      
      if (conditions.length > 0) {
        sql += ' WHERE ' + conditions.join(' AND ');
      }
    }
    
    // Add ORDER BY clause
    if (sortBy) {
      sql += ` ORDER BY ${sortBy} ${sortOrder || 'ASC'}`;
    }
    
    // Add LIMIT clause
    if (limit) {
      sql += ` LIMIT ${limit}`;
    }
    
    return sql;
  },
  
  // Validate query before execution
  validateQuery: (queryData) => {
    const errors = [];
    
    if (!queryData.table) {
      errors.push('Table selection is required');
    }
    
    // Validate filters
    if (queryData.filters) {
      queryData.filters.forEach((filter, index) => {
        if (filter.column && !filter.value && filter.operator !== 'is_null' && filter.operator !== 'is_not_null') {
          errors.push(`Filter ${index + 1}: Value is required`);
        }
      });
    }
    
    return {
      isValid: errors.length === 0,
      errors
    };
  }
};

// Utility functions
export const utils = {
  // Format error messages for display
  formatError: (error) => {
    if (error.response?.data?.message) {
      return error.response.data.message;
    }
    if (error.response?.data?.detail) {
      return error.response.data.detail;
    }
    if (error.message) {
      return error.message;
    }
    return 'An unexpected error occurred';
  },
  
  // Download file from blob
  downloadBlob: (blob, filename) => {
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
  },
  
  // Format data for display
  formatCellValue: (value, type) => {
    if (value === null || value === undefined) {
      return '-';
    }
    
    switch (type) {
      case 'currency':
        return new Intl.NumberFormat('en-US', {
          style: 'currency',
          currency: 'USD'
        }).format(value);
      case 'number':
        return new Intl.NumberFormat('en-US').format(value);
      case 'date':
        return new Date(value).toLocaleDateString();
      case 'datetime':
        return new Date(value).toLocaleString();
      case 'boolean':
        return value ? 'Yes' : 'No';
      default:
        return String(value);
    }
  }
};

export default api; 