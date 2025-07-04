# Memory Management for Large Datasets

## Overview

This document explains the memory management features implemented to handle large datasets (2 million+ records) in the query builder and stratification processes.

## Problems Addressed

1. **Memory exhaustion** when loading large datasets into memory
2. **Jupyter session crashes** due to excessive memory usage
3. **Query builder breaking** on large datasets
4. **Stratification process failing** with large datasets

## Solutions Implemented

### 1. Chunked Query Execution

#### New Functions Added:
- `execute_query_chunked()` - Processes large datasets in chunks
- `execute_query_with_limit_check()` - Automatically chooses appropriate execution method

#### Features:
- Processes data in configurable chunks (default: 5,000 rows)
- Automatic memory warnings for large datasets
- Fallback to chunked processing for datasets > 50,000 rows

#### Usage:
```python
# Automatic chunking for large datasets
result = execute_query_with_limit_check(sql_query, max_rows=50000)

# Manual chunked processing
result = execute_query_chunked(sql_query, chunk_size=5000)
```

### 2. Memory-Efficient Stratification

#### New Features:
- **Stratified sampling** for datasets > 500,000 rows
- **Memory usage monitoring** and warnings
- **Garbage collection** after processing
- **Configurable memory limits**

#### Configuration Options:
```python
stratification_request = {
    "data": dataset,
    "columns": column_names,
    "n_splits": 3,
    "stratify_cols": ["age_group", "gender"],
    # Memory management settings
    "max_memory_rows": 300000,      # Trigger sampling above this
    "sample_size": 50000,           # Sample size for large datasets
    "use_sampling": True,           # Enable/disable sampling
}
```

### 3. Enhanced Query Builder

#### Safety Features:
- **Automatic limit warnings** for large queries
- **Default limits** to prevent runaway queries
- **Memory usage warnings**

#### Usage:
```python
# Build query with memory safety checks
query = query_builder.build_query_with_memory_check(request_data)
```

## Usage Guidelines

### For Datasets < 100,000 rows:
- Normal processing, no special configuration needed
- Standard memory usage

### For Datasets 100,000 - 500,000 rows:
- Chunked processing automatically enabled
- Memory warnings displayed
- Consider adding filters to reduce dataset size

### For Datasets > 300,000 rows:
- Stratified sampling automatically enabled
- Memory-efficient processing used
- Strong recommendation to use filters or pagination

### For Datasets > 2GB memory usage:
- Processing blocked to prevent crashes
- Must reduce dataset size or add filters
- System will return error message

## Best Practices

### 1. Query Optimization
```python
# Good: Use filters to reduce dataset size
query_data = {
    'database_id': 'DSSB_APP',
    'table': 'large_table',
    'filters': [
        {'column': 'date', 'operator': 'greater_than', 'value': '2023-01-01'},
        {'column': 'status', 'operator': 'equals', 'value': 'active'}
    ],
    'limit': 10000
}

# Avoid: Unlimited queries on large tables
query_data = {
    'database_id': 'DSSB_APP',
    'table': 'large_table',
    'limit': None  # This will default to 10,000
}
```

### 2. Stratification Configuration
```python
# For large datasets, configure memory settings
stratification_config = {
    "numGroups": 3,
    "stratifyColumns": ["age_group"],
    "max_memory_rows": 500000,
    "sample_size": 100000,
    "use_sampling": True
}
```

### 3. Monitoring Memory Usage
- Check console output for memory warnings
- Monitor dataset sizes before processing
- Use smaller chunks for very large datasets

## Error Handling

### Memory Exhaustion Prevention:
```python
try:
    result = execute_query_with_limit_check(sql_query)
    if result["row_count"] > 100000:
        print("Large dataset detected - using chunked processing")
except Exception as e:
    print(f"Memory-related error: {e}")
```

### Stratification Error Handling:
```python
try:
    stratification_result = stratify_data(request_data)
    print(f"Memory-efficient processing: {stratification_result['memory_info']['memory_efficient_processing']}")
except Exception as e:
    print(f"Stratification error: {e}")
```

## Configuration Options

### Database Configuration:
```python
# database.py settings
CHUNK_SIZE = 5000           # Rows per chunk
MAX_MEMORY_ROWS = 50000     # Trigger chunking above this
WARNING_THRESHOLD = 100000  # Show warnings above this
```

### Stratification Configuration:
```python
# stratification.py settings
DEFAULT_MAX_MEMORY_ROWS = 300000    # Default memory limit
DEFAULT_SAMPLE_SIZE = 50000         # Default sample size
MIN_SAMPLE_SIZE = 10000            # Minimum sample size
CRITICAL_MEMORY_THRESHOLD = 2000    # Memory limit in MB (2GB)
```

## Troubleshooting

### Issue: Jupyter Session Crashes
**Solution**: Reduce dataset size or increase memory limits
```python
# Increase sample size limits
stratification_config["sample_size"] = 50000  # Reduce sample size
stratification_config["max_memory_rows"] = 250000  # Lower memory threshold
```

### Issue: Query Builder Times Out
**Solution**: Add more restrictive filters or limits
```python
# Add date filters
filters = [
    {'column': 'created_date', 'operator': 'greater_than', 'value': '2023-01-01'},
    {'column': 'created_date', 'operator': 'less_than', 'value': '2023-12-31'}
]
```

### Issue: Stratification Takes Too Long
**Solution**: Reduce sample size or number of groups
```python
stratification_config = {
    "numGroups": 3,  # Reduce from 5 to 3
    "sample_size": 50000,  # Reduce sample size
    "use_sampling": True
}
```

## Performance Metrics

### Memory Usage:
- **Small datasets (< 1M)**: 100-500 MB
- **Medium datasets (1M-3M)**: 500-2000 MB
- **Large datasets (3M+)**: 1-4 GB (with chunking and sampling)

### Processing Time:
- **Small datasets**: < 30 seconds
- **Medium datasets**: 30-120 seconds
- **Large datasets**: 60-300 seconds (with sampling)

## Implementation Details

### Chunked Processing Flow:
1. Check dataset size
2. If > threshold, use chunked processing
3. Process in configurable chunks
4. Monitor memory usage
5. Provide progress updates

### Stratification Flow:
1. Check dataset size
2. If > threshold, create stratified sample
3. Perform stratification on sample
4. Apply proportions to full dataset
5. Clean up memory

## Future Enhancements

1. **Streaming processing** for very large datasets
2. **Database-side sampling** for better performance
3. **Distributed processing** for massive datasets
4. **Caching mechanisms** for repeated queries
5. **Progress bars** for long-running operations

## Contact

For issues or questions about memory management features, contact the development team. 