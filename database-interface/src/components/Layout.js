import React from 'react';
import { NavLink } from 'react-router-dom';
import { 
  BarChart3, 
  Database, 
  Search, 
  Settings, 
  Home 
} from 'lucide-react';

const Layout = ({ children }) => {
  const navigation = [
    { name: 'Панель управления', href: '/', icon: Home },
    { name: 'Конструктор запросов', href: '/query-builder', icon: Search },
    { name: 'Просмотр данных', href: '/data-viewer', icon: BarChart3 },
    { name: 'Настройки', href: '/settings', icon: Settings },
  ];

  return (
    <div className="app-layout">
      <div className="sidebar">
        <div className="sidebar-header">
          <h1 className="sidebar-title">
            <Database className="nav-icon" style={{ display: 'inline', marginRight: '0.5rem' }} />
            DataQuery Pro
          </h1>
        </div>
        <nav>
          <ul className="nav-menu">
            {navigation.map((item) => {
              const Icon = item.icon;
              return (
                <li key={item.name} className="nav-item">
                  <NavLink
                    to={item.href}
                    className={({ isActive }) => 
                      `nav-link ${isActive ? 'active' : ''}`
                    }
                  >
                    <Icon className="nav-icon" />
                    {item.name}
                  </NavLink>
                </li>
              );
            })}
          </ul>
        </nav>
      </div>
      <main className="main-content">
        {children}
      </main>
    </div>
  );
};

export default Layout; 