import React, { useState, useEffect } from 'react';
import { 
  Plus, 
  Trash2, 
  Play, 
  Database, 
  Filter,
  Download,
  RefreshCw,
  Layers,
  Users,
  Target
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

  // Pagination state for query results
  const [resultsCurrentPage, setResultsCurrentPage] = useState(1);
  const [resultsRowsPerPage, setResultsRowsPerPage] = useState(100);

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

  // Stratification state
  const [showStratificationModal, setShowStratificationModal] = useState(false);
  const [stratificationConfig, setStratificationConfig] = useState({
    enabled: false,
    numGroups: 3,
    stratifyColumns: [],
    theoryBaseName: '',
    theoryDescription: '',
    theoryStartDate: '',
    theoryEndDate: '',
    iinColumn: '',
    randomSeed: 42,
    groupFields: {}
  });
  const [isStratifying, setIsStratifying] = useState(false);
  const [stratificationResults, setStratificationResults] = useState(null);

  useEffect(() => {
    loadDatabases();
  }, []);

  // Rest of your existing functions would go here...
  // This is just to show the clean structure without progress/websocket code

  return (
    <div>
      {/* Your existing JSX but with simple loading instead of progress bars */}
      {isLoading && (
        <div style={{ padding: '1rem', textAlign: 'center', color: '#6b7280' }}>
          🔄 Выполняется запрос...
        </div>
      )}
      {/* Rest of your UI */}
    </div>
  );
};

export default QueryBuilder;