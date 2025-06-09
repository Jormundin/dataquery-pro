# Frontend Documentation - Corporate Database Interface

## Overview
A modern React-based web application that provides a user-friendly interface for corporate database interactions. Designed for non-SQL users to interact with databases through visual filters and query builders.

## 🚀 Quick Start

### Prerequisites
- Node.js (v14 or higher)
- npm or yarn package manager
- Access to the backend API

### Installation
```bash
cd database-interface
npm install
npm start
```

The application will be available at `http://localhost:3000`

## 📁 Project Structure

```
database-interface/
├── public/
│   ├── index.html
│   └── favicon.ico
├── src/
│   ├── components/
│   │   ├── Layout.js          # Main layout with sidebar navigation
│   │   ├── Dashboard.js       # Dashboard with statistics and overview
│   │   ├── QueryBuilder.js    # Visual SQL query builder
│   │   ├── DataViewer.js      # Data browsing and viewing
│   │   └── Settings.js        # Application settings and configuration
│   ├── pages/                 # Page components (future expansion)
│   ├── services/
│   │   └── api.js            # API service layer for backend communication
│   ├── App.js                # Main application component with routing
│   ├── App.css               # Global styles and component styling
│   └── index.js              # Application entry point
├── package.json
└── README.md
```

## 🎯 Key Features

### 1. Dashboard
- **Statistics Overview**: Key metrics and database statistics
- **Recent Queries**: History of executed queries with status
- **Database Status**: Real-time connection status monitoring
- **Quick Actions**: Shortcut buttons for common operations

### 2. Visual Query Builder
- **Database Selection**: Dropdown to choose target database
- **Table Selection**: Dynamic table loading based on selected database
- **Column Selection**: Multi-select for choosing columns to retrieve
- **Dynamic Filters**: Add/remove filters with various operators (=, >, <, LIKE, etc.)
- **Sorting Options**: Configurable sorting by multiple columns
- **SQL Preview**: Real-time SQL query generation
- **Results Display**: Formatted table view of query results

### 3. Data Viewer
- **Table Browsing**: Navigate through database tables
- **Search Functionality**: Filter data across columns
- **Pagination**: Handle large datasets efficiently
- **Sorting**: Click column headers to sort
- **Row Selection**: Select multiple rows for operations
- **CSV Export**: Export filtered data to CSV format

### 4. Settings Management
- **Database Connections**: Configure multiple database connections
- **API Settings**: Backend URL and timeout configurations
- **User Preferences**: Language, theme, and display options
- **Connection Testing**: Validate database connections

## 🛠 Technical Architecture

### State Management
- Uses React hooks (`useState`, `useEffect`) for local state management
- No external state management library (Redux/Context) currently implemented
- Component-level state for UI interactions

### Routing
- React Router v6 for navigation
- Protected routes can be easily implemented
- Clean URL structure with browser history

### Styling Approach
- Custom CSS with modern design principles
- Responsive design for desktop and tablet
- Corporate-friendly color scheme (blues and grays)
- Consistent spacing and typography

### API Integration
- Centralized API service in `services/api.js`
- Axios for HTTP requests
- Error handling and loading states
- Configurable base URL and timeouts

## 🌍 Localization

### Current Status
- **Russian Translation**: Partially implemented
  - ✅ Navigation menu (Layout.js)
  - ✅ Dashboard (complete)
  - ⚠️ Query Builder (partial)
  - ❌ Data Viewer (pending)
  - ❌ Settings (pending)

### Adding Translations
1. Update component files with translated strings
2. Consider implementing i18n library for better management
3. Add language switcher in Settings

## 🔧 Development Workflow

### Running the Application
```bash
# Development mode
npm start

# Production build
npm run build

# Run tests
npm test
```

### Common Development Tasks

#### Adding New Components
1. Create component file in `src/components/`
2. Add routing in `App.js` if needed
3. Update navigation in `Layout.js`
4. Add API endpoints in `services/api.js`

#### Styling Guidelines
- Use consistent class naming (BEM-like approach)
- Follow existing color scheme
- Maintain responsive design principles
- Test on different screen sizes

#### API Integration
- All API calls should go through `services/api.js`
- Handle loading and error states consistently
- Use try-catch blocks for error handling

## 🐛 Common Issues and Solutions

### React 18 Compatibility
**Issue**: ReactDOM.render is deprecated
**Solution**: Updated to use createRoot API in index.js

### ESLint Warnings
**Issue**: Unused imports and variables
**Solution**: Regular cleanup of unused code

### CORS Issues
**Issue**: Cross-origin requests blocked
**Solution**: Ensure backend CORS configuration allows frontend domain

### Performance Issues
**Issue**: Large datasets causing slow rendering
**Solution**: Implement pagination and virtualization for large tables

## 📦 Dependencies

### Core Dependencies
```json
{
  "react": "^18.2.0",
  "react-dom": "^18.2.0",
  "react-router-dom": "^6.8.1",
  "axios": "^1.3.4"
}
```

### UI Dependencies
```json
{
  "lucide-react": "^0.336.0",
  "@headlessui/react": "^1.7.14",
  "@heroicons/react": "^2.0.16"
}
```

## 🚀 Deployment

### Production Build
```bash
npm run build
```

### Environment Configuration
Create `.env.production` file:
```
REACT_APP_API_URL=https://your-backend-api.com
REACT_APP_ENVIRONMENT=production
```

### Deployment Options
- **Static Hosting**: Netlify, Vercel, GitHub Pages
- **Traditional Hosting**: Apache, Nginx
- **Container**: Docker deployment
- **Cloud**: AWS S3 + CloudFront, Azure Static Web Apps

## 🔒 Security Considerations

### Authentication
- Ready for JWT token integration
- Secure storage of authentication tokens
- Automatic token refresh capability

### Data Security
- No sensitive data stored in localStorage
- HTTPS enforcement in production
- Input validation and sanitization

## 🎨 UI/UX Features

### Design System
- Modern corporate aesthetic
- Consistent iconography using Lucide React
- Professional color palette
- Accessible design principles

### User Experience
- Intuitive navigation with clear hierarchy
- Loading states for all async operations
- Error messages with actionable feedback
- Responsive design for various screen sizes

## 📈 Future Enhancements

### Planned Features
- Advanced query templates and saved queries
- Real-time data updates with WebSocket
- Advanced filtering and sorting options
- Data visualization charts and graphs
- User role management and permissions
- Advanced export options (Excel, PDF)

### Technical Improvements
- Implement proper state management (Redux Toolkit)
- Add comprehensive testing suite
- Implement PWA capabilities
- Add dark/light theme toggle
- Performance optimizations with React.memo

## 📞 Support and Maintenance

### Debugging
- Use React Developer Tools
- Check browser console for errors
- Monitor network requests in DevTools
- Check API response formats

### Monitoring
- Implement error tracking (Sentry)
- Add performance monitoring
- Track user interactions (Analytics)

### Updates
- Regular dependency updates
- Security patch management
- Feature enhancement cycles

---

**Version**: 1.0.0  
**Last Updated**: December 2024  
**Maintainer**: Development Team 