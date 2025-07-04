"""
Stratification module for creating balanced data groups
Integrated from external stratification service
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import StratifiedKFold, StratifiedShuffleSplit
from scipy.stats import ks_2samp, chi2_contingency
from typing import List, Dict, Any, Tuple, Optional
from pydantic import BaseModel, Field, ValidationError
import math
import gc


class StratificationRequest(BaseModel):
    data: list  # The DataFrame data as a list of records (dicts)
    columns: list  # List of column names corresponding to the data
    n_splits: int = Field(None, ge=2, le=10, description="Number of stratified groups (2-10). Not required if split_sizes is provided.")
    stratify_cols: list = Field(..., description="List of column names for stratification.")
    replace_nan: bool = True
    random_state: int = 42
    test_size: float = Field(None, ge=0.0, le=1.0, description="Proportion of the dataset to include in the test sample (0.0 - 1.0).")
    split_sizes: list = Field(None, description="List of proportions for custom splits (e.g., [0.9, 0.1] for 90%/10% split). Must sum to 1.0.")
    ks_test_columns: list = Field(None, description="List of specific columns to monitor for statistical tests (KS test for numeric, Chi-square for categorical). If None, all numeric columns will be used.")
    min_p_value: float = Field(None, ge=0.0, le=1.0, description="Minimum p-value threshold for statistical tests. Stratification will iterate until this threshold is met or exceeded.")
    max_iterations: int = Field(100, ge=1, le=1000, description="Maximum number of iterations to attempt when trying to meet p-value threshold.")
    # New fields for memory management
    max_memory_rows: int = Field(1500000, ge=100000, le=5000000, description="Maximum number of rows to process in memory before using sampling.")
    sample_size: int = Field(500000, ge=50000, le=1000000, description="Sample size to use for large datasets.")
    use_sampling: bool = Field(True, description="Whether to use sampling for large datasets.")
   
    def __init__(self, **data):
        super().__init__(**data)
        # Validate that either n_splits or split_sizes is provided
        if self.n_splits is None and self.split_sizes is None:
            raise ValueError("Either 'n_splits' or 'split_sizes' must be provided.")
        if self.n_splits is not None and self.split_sizes is not None:
            raise ValueError("Provide either 'n_splits' or 'split_sizes', not both.")
        if self.split_sizes is not None:
            if len(self.split_sizes) < 2:
                raise ValueError("split_sizes must contain at least 2 proportions.")
            if not all(0 < size < 1 for size in self.split_sizes):
                raise ValueError("All split sizes must be between 0 and 1.")
            if abs(sum(self.split_sizes) - 1.0) > 1e-6:
                raise ValueError("Split sizes must sum to 1.0.")
            # Set n_splits based on split_sizes length for compatibility
            self.n_splits = len(self.split_sizes)
       
        # Validate min_p_value and ks_test_columns relationship
        if self.min_p_value is not None and self.ks_test_columns is None:
            raise ValueError("When min_p_value is specified, ks_test_columns must also be provided.")


def calculate_statistical_test(original_data: pd.DataFrame, split_data: pd.DataFrame, column_name: str) -> Tuple[float, float, str]:
    """
    Calculate appropriate statistical test based on column type.
    Returns (statistic, p_value, test_type)
    """
    original_col = original_data[column_name]
    split_col = split_data[column_name]
   
    # Check if column is numeric
    if pd.api.types.is_numeric_dtype(original_col):
        # Use Kolmogorov-Smirnov test for numeric data
        statistic, p_value = ks_2samp(original_col, split_col)
        return statistic, p_value, 'ks_test'
    else:
        # Use Chi-square test for categorical data
        try:
            # Create contingency table
            original_counts = original_col.value_counts()
            split_counts = split_col.value_counts()
           
            # Get all unique categories
            all_categories = set(original_counts.index) | set(split_counts.index)
           
            # Create aligned counts (fill missing categories with 0)
            original_aligned = [original_counts.get(cat, 0) for cat in all_categories]
            split_aligned = [split_counts.get(cat, 0) for cat in all_categories]
           
            # Create contingency table
            contingency_table = np.array([original_aligned, split_aligned])
           
            # Perform chi-square test
            if contingency_table.sum() > 0 and len(all_categories) > 1:
                chi2_stat, p_value, dof, expected = chi2_contingency(contingency_table)
                return chi2_stat, p_value, 'chi2_test'
            else:
                # If no variation or insufficient data, return high p-value
                return 0.0, 1.0, 'chi2_test'
               
        except Exception as e:
            # If chi-square test fails, return low p-value to be conservative
            return float('inf'), 0.0, 'chi2_test_failed'


def perform_stratification(df: pd.DataFrame, y: pd.Series, request: StratificationRequest, iteration_seed: Optional[int] = None) -> Tuple[List[pd.DataFrame], List[Dict]]:
    """
    Perform a single stratification operation and return splits with statistical test results.
    """
    X = df.drop(columns=request.stratify_cols)
    seed = iteration_seed if iteration_seed is not None else request.random_state
   
    # Determine which columns to use for statistical testing
    if request.ks_test_columns is not None:
        test_columns = request.ks_test_columns
    else:
        # Default to all numeric columns if none specified
        test_columns = X.select_dtypes(include=np.number).columns.tolist()
   
    if request.split_sizes is not None:
        # Custom split sizes - use multiple StratifiedShuffleSplit operations
        splits = []
        test_scores = []
        remaining_df = df.copy()
        remaining_y = y.copy()
       
        for i, split_size in enumerate(request.split_sizes):
            if i == len(request.split_sizes) - 1:
                # Last split gets all remaining data
                split_df = remaining_df.reset_index(drop=True)
            else:
                # Calculate the proportion relative to remaining data
                relative_size = split_size / sum(request.split_sizes[i:])
               
                sss = StratifiedShuffleSplit(
                    n_splits=1,
                    test_size=relative_size,
                    random_state=seed + i
                )
                remaining_index, split_index = next(sss.split(remaining_df, remaining_y))
               
                split_df = remaining_df.iloc[split_index].reset_index(drop=True)
                remaining_df = remaining_df.iloc[remaining_index].reset_index(drop=True)
                remaining_y = remaining_y.iloc[remaining_index].reset_index(drop=True)
           
            splits.append(split_df)
           
            # Calculate statistical tests for specified columns
            test_dict = {}
            for col in test_columns:
                if col in df.columns:
                    statistic, p_value, test_type = calculate_statistical_test(df, split_df, col)
                    test_dict[col] = {
                        'p_value': p_value,
                        'statistic': statistic,
                        'test_type': test_type
                    }
            test_scores.append(test_dict)
    else:
        # Equal splits - use StratifiedKFold
        skf = StratifiedKFold(n_splits=request.n_splits, shuffle=True, random_state=seed)
        splits = []
        test_scores = []

        for _, test_index in skf.split(X, y):
            split_df = df.iloc[test_index].reset_index(drop=True)
            splits.append(split_df)

            # Calculate statistical tests for specified columns
            test_dict = {}
            for col in test_columns:
                if col in df.columns:
                    statistic, p_value, test_type = calculate_statistical_test(df, split_df, col)
                    test_dict[col] = {
                        'p_value': p_value,
                        'statistic': statistic,
                        'test_type': test_type
                    }
            test_scores.append(test_dict)
   
    return splits, test_scores


def check_p_value_criteria(ks_scores: List[Dict], ks_test_columns: List[str], min_p_value: float) -> bool:
    """
    Check if all specified columns meet the minimum p-value threshold across all splits.
    """
    for split_ks in ks_scores:
        for col in ks_test_columns:
            if col in split_ks and split_ks[col]['p_value'] < min_p_value:
                return False
    return True


def get_min_p_values(ks_scores: List[Dict], ks_test_columns: List[str]) -> Dict[str, Optional[float]]:
    """
    Get the minimum p-values for each specified column across all splits.
    """
    min_p_values = {}
    for col in ks_test_columns:
        min_p = float('inf')
        for split_ks in ks_scores:
            if col in split_ks:
                min_p = min(min_p, split_ks[col]['p_value'])
        min_p_values[col] = min_p if min_p != float('inf') else None
    return min_p_values


def create_stratified_sample(df: pd.DataFrame, stratify_cols: List[str], sample_size: int, random_state: int = 42) -> pd.DataFrame:
    """
    Create a stratified sample from a large DataFrame to reduce memory usage.
    """
    try:
        # Combine stratification columns
        y = df[stratify_cols].astype(str).agg('_'.join, axis=1)
        
        # Calculate minimum samples needed per stratum
        unique_strata = y.nunique()
        min_samples_per_stratum = max(10, math.ceil(sample_size / unique_strata))
        
        # Use stratified sampling
        if len(df) <= sample_size:
            return df.copy()
        
        # Create stratified sample
        sample_indices = []
        for stratum in y.unique():
            stratum_indices = df[y == stratum].index
            n_samples = min(len(stratum_indices), min_samples_per_stratum)
            
            if n_samples > 0:
                sampled_indices = np.random.RandomState(random_state).choice(
                    stratum_indices, size=n_samples, replace=False
                )
                sample_indices.extend(sampled_indices)
        
        # If we don't have enough samples, add more randomly
        if len(sample_indices) < sample_size:
            remaining_indices = df.index.difference(sample_indices)
            n_additional = min(sample_size - len(sample_indices), len(remaining_indices))
            if n_additional > 0:
                additional_indices = np.random.RandomState(random_state + 1).choice(
                    remaining_indices, size=n_additional, replace=False
                )
                sample_indices.extend(additional_indices)
        
        return df.loc[sample_indices].reset_index(drop=True)
        
    except Exception as e:
        print(f"Error creating stratified sample: {e}")
        # Fallback to simple random sampling
        return df.sample(n=min(sample_size, len(df)), random_state=random_state).reset_index(drop=True)


def memory_efficient_stratification(df: pd.DataFrame, y: pd.Series, request: StratificationRequest) -> Tuple[List[pd.DataFrame], List[Dict]]:
    """
    Perform memory-efficient stratification for large datasets.
    """
    original_size = len(df)
    print(f"Starting stratification for {original_size} rows...")
    
    # Check if we need to use sampling
    if request.use_sampling and original_size > request.max_memory_rows:
        print(f"Large dataset detected ({original_size} rows). Using stratified sampling to {request.sample_size} rows...")
        
        # Create stratified sample
        sample_df = create_stratified_sample(df, request.stratify_cols, request.sample_size, request.random_state)
        sample_y = sample_df[request.stratify_cols].astype(str).agg('_'.join, axis=1)
        
        print(f"Sample created with {len(sample_df)} rows")
        
        # Perform stratification on the sample
        sample_splits, sample_test_scores = perform_stratification(sample_df, sample_y, request)
        
        # Now apply the stratification proportions to the full dataset
        print("Applying stratification proportions to full dataset...")
        full_splits = []
        full_test_scores = []
        
        # Calculate the proportion of each stratum in each split
        stratum_proportions = {}
        for i, split in enumerate(sample_splits):
            split_y = split[request.stratify_cols].astype(str).agg('_'.join, axis=1)
            stratum_counts = split_y.value_counts()
            
            for stratum, count in stratum_counts.items():
                if stratum not in stratum_proportions:
                    stratum_proportions[stratum] = {}
                stratum_proportions[stratum][i] = count / len(split)
        
        # Apply proportions to full dataset
        for i in range(len(sample_splits)):
            full_split_indices = []
            
            for stratum in y.unique():
                stratum_indices = df[y == stratum].index.tolist()
                if stratum in stratum_proportions:
                    target_proportion = stratum_proportions[stratum].get(i, 0)
                    n_samples = int(len(stratum_indices) * target_proportion)
                    if n_samples > 0:
                        sampled_indices = np.random.RandomState(request.random_state + i).choice(
                            stratum_indices, size=min(n_samples, len(stratum_indices)), replace=False
                        )
                        full_split_indices.extend(sampled_indices)
            
            if full_split_indices:
                full_split = df.loc[full_split_indices].reset_index(drop=True)
                full_splits.append(full_split)
                
                # Calculate test statistics for the full split
                test_columns = request.ks_test_columns if request.ks_test_columns else df.select_dtypes(include=np.number).columns.tolist()
                test_dict = {}
                
                # Use a sample for statistical testing if the full split is too large
                if len(full_split) > 50000:
                    test_sample = full_split.sample(n=min(50000, len(full_split)), random_state=request.random_state)
                    df_sample = df.sample(n=min(50000, len(df)), random_state=request.random_state)
                    
                    for col in test_columns:
                        if col in df.columns:
                            try:
                                statistic, p_value, test_type = calculate_statistical_test(df_sample, test_sample, col)
                                test_dict[col] = {
                                    'p_value': p_value,
                                    'statistic': statistic,
                                    'test_type': test_type
                                }
                            except Exception as e:
                                print(f"Error calculating statistics for column {col}: {e}")
                                test_dict[col] = {
                                    'p_value': 0.5,
                                    'statistic': 0.0,
                                    'test_type': 'error'
                                }
                else:
                    for col in test_columns:
                        if col in df.columns:
                            try:
                                statistic, p_value, test_type = calculate_statistical_test(df, full_split, col)
                                test_dict[col] = {
                                    'p_value': p_value,
                                    'statistic': statistic,
                                    'test_type': test_type
                                }
                            except Exception as e:
                                print(f"Error calculating statistics for column {col}: {e}")
                                test_dict[col] = {
                                    'p_value': 0.5,
                                    'statistic': 0.0,
                                    'test_type': 'error'
                                }
                
                full_test_scores.append(test_dict)
        
        # Clean up memory
        del sample_df, sample_y, sample_splits, sample_test_scores
        gc.collect()
        
        print(f"Memory-efficient stratification completed. Created {len(full_splits)} groups from {original_size} rows.")
        return full_splits, full_test_scores
        
    else:
        # Use regular stratification for smaller datasets
        print(f"Using regular stratification for {original_size} rows...")
        return perform_stratification(df, y, request)


def stratify_data(request_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main stratification function that replicates the /stratify endpoint functionality
    """
    try:
        # Create StratificationRequest from input data
        request = StratificationRequest(**request_data)
    except (ValidationError, ValueError) as e:
        raise ValueError(f"Invalid stratification request: {str(e)}")

    # Reconstruct the DataFrame from the input data
    try:
        print(f"Reconstructing DataFrame with {len(request.data)} rows and {len(request.columns)} columns...")
        df = pd.DataFrame(data=request.data, columns=request.columns)
        
        # Add memory usage information and safety checks
        memory_usage_mb = df.memory_usage(deep=True).sum() / 1024 / 1024
        print(f"DataFrame memory usage: {memory_usage_mb:.2f} MB")
        
        # Critical memory threshold - prevent crashes only at extreme sizes
        if memory_usage_mb > 8000:  # 8GB threshold for critical failure
            raise ValueError(f"Dataset exceeds system limits ({memory_usage_mb:.1f} MB). System cannot process datasets larger than 8GB.")
        elif memory_usage_mb > 4000:  # 4GB warning
            print(f"Large dataset detected ({memory_usage_mb:.1f} MB). Using memory-efficient processing.")
        
        # Check if we need to enable memory-efficient processing for very large datasets
        if len(df) > 1500000:
            print(f"Very large dataset detected ({len(df)} rows). Enabling memory-efficient processing.")
            request.use_sampling = True
        elif len(df) > 2000000:
            print(f"Processing {len(df)} rows using optimized algorithms.")
            
    except Exception as e:
        raise ValueError(f"Error reconstructing DataFrame: {e}")

    # Validate n_splits (after it's been set by __init__ if split_sizes was provided)
    if not (2 <= request.n_splits <= 10):
        if request.split_sizes is not None:
            raise ValueError("Number of split_sizes must be between 2 and 10.")
        else:
            raise ValueError("n_splits must be between 2 and 10.")

    # Validate stratify_cols
    stratify_cols_list = request.stratify_cols
    if not stratify_cols_list:
        raise ValueError("Please provide at least one stratification column.")
    for col in stratify_cols_list:
        if col not in df.columns:
            raise ValueError(f"Column '{col}' not found in the DataFrame.")

    # Validate ks_test_columns if provided
    if request.ks_test_columns is not None:
        for col in request.ks_test_columns:
            if col not in df.columns:
                raise ValueError(f"Test column '{col}' not found in the DataFrame.")

    # Handle NaN values in stratification columns
    if request.replace_nan:
        for col in stratify_cols_list:
            if df[col].isnull().any():
                if df[col].dtype in [np.float64, np.int64]:
                    df[col].fillna(0, inplace=True)
                elif df[col].dtype == object:
                    df[col].fillna('None', inplace=True)
                else:
                    df[col].fillna('None', inplace=True)

    # Combine stratification columns
    y = df[stratify_cols_list].astype(str).agg('_'.join, axis=1)

    # Remove strata with insufficient samples
    min_samples = request.n_splits
    if request.test_size and request.test_size > 0:
        min_samples += 1  # Need at least one sample for the test set
    value_counts = y.value_counts()
    insufficient_strata = value_counts[value_counts < min_samples].index.tolist()

    if insufficient_strata:
        print(f"Removing {len(insufficient_strata)} strata with insufficient samples...")
        df = df[~y.isin(insufficient_strata)]
        y = y[~y.isin(insufficient_strata)]

    if y.nunique() < 2:
        raise ValueError("Not enough unique strata after removing insufficient ones.")

    # Split off test set if test_size is specified
    if request.test_size and request.test_size > 0:
        sss = StratifiedShuffleSplit(n_splits=1, test_size=request.test_size, random_state=request.random_state)
        train_index, test_index = next(sss.split(df, y))
        test_df = df.iloc[test_index].reset_index(drop=True)
        df = df.iloc[train_index].reset_index(drop=True)
        y = y.iloc[train_index].reset_index(drop=True)
    else:
        test_df = None

    # Perform stratified splitting on the remaining data
    X = df.drop(columns=stratify_cols_list)
   
    # Determine which columns to use for KS testing
    if request.ks_test_columns is not None:
        test_columns = request.ks_test_columns
    else:
        test_columns = X.select_dtypes(include=np.number).columns.tolist()
   
    # Perform stratification with optional iterative p-value checking
    if request.min_p_value is not None and request.ks_test_columns is not None:
        # Iterative approach to meet p-value criteria
        best_splits = None
        best_ks_scores = None
        best_min_p_values = None
        iteration = 0
        criteria_met = False
       
        while iteration < request.max_iterations and not criteria_met:
            # Use different random seed for each iteration
            iteration_seed = request.random_state + iteration * 1000
            
            # Create a copy of the request with the new seed
            iteration_request = request.copy()
            iteration_request.random_state = iteration_seed
           
            # Perform stratification using memory-efficient method
            splits, test_scores = memory_efficient_stratification(df, y, iteration_request)
           
            # Check if p-value criteria are met
            criteria_met = check_p_value_criteria(test_scores, test_columns, request.min_p_value)
           
            # Get minimum p-values for tracking
            min_p_values = get_min_p_values(test_scores, test_columns)
           
            # Keep track of the best result so far (highest minimum p-values)
            if best_splits is None or (best_min_p_values and min_p_values):
                current_min = min([p for p in min_p_values.values() if p is not None])
                best_min = min([p for p in best_min_p_values.values() if p is not None]) if best_min_p_values else 0
               
                if current_min > best_min:
                    best_splits = splits
                    best_ks_scores = test_scores
                    best_min_p_values = min_p_values
           
            iteration += 1
       
        # Use the best result found
        splits = best_splits
        test_scores = best_ks_scores
       
        # Add iteration information to response
        iteration_info = {
            'iterations_performed': iteration,
            'criteria_met': criteria_met,
            'target_p_value': request.min_p_value,
            'achieved_min_p_values': best_min_p_values,
            'max_iterations': request.max_iterations
        }
    else:
        # Single stratification without p-value criteria - use memory-efficient method
        splits, test_scores = memory_efficient_stratification(df, y, request)
        iteration_info = None

    # Prepare the response
    stratified_data = []
    total_rows = df.shape[0]
   
    for i, split_df in enumerate(splits):
        # Handle JSON conversion for large datasets
        if len(split_df) > 100000:
            print(f"Split {i+1} contains {len(split_df)} rows. Using efficient JSON conversion.")
            # For very large splits, use more efficient conversion
            split_data_json = split_df.head(100000).to_dict(orient='records')
            print(f"Note: Split {i+1} JSON response limited to first 100,000 rows for efficiency.")
        else:
            split_data_json = split_df.to_dict(orient='records')
        actual_proportion = split_df.shape[0] / total_rows
       
        stratum_info = {
            'stratum': i + 1,
            'data': split_data_json,
            'num_rows': split_df.shape[0],
            'proportion': round(actual_proportion, 4),
            'test_statistics': test_scores[i]
        }
       
        # Add requested proportion if custom split sizes were used
        if request.split_sizes is not None:
            stratum_info['requested_proportion'] = request.split_sizes[i]
           
        stratified_data.append(stratum_info)

    response = {
        'n_splits': request.n_splits,
        'stratify_cols': stratify_cols_list,
        'ks_test_columns': test_columns,
        'stratified_groups': stratified_data,
        'total_rows': total_rows,
        'message': 'Stratification successful.',
        'memory_info': {
            'original_rows': len(request.data),
            'processed_rows': total_rows,
            'memory_efficient_processing': request.use_sampling and len(request.data) > request.max_memory_rows
        }
    }
   
    # Add split method information
    if request.split_sizes is not None:
        response['split_method'] = 'custom_proportions'
        response['requested_split_sizes'] = request.split_sizes
    else:
        response['split_method'] = 'equal_kfold'

    # Include test set in the response if applicable
    if test_df is not None:
        # Convert test DataFrame to JSON
        test_data_json = test_df.to_dict(orient='records')
        # Calculate KS statistics for the test set using specified columns
        ks_dict_test = {}
        for col in test_columns:
            if col in df.columns:
                statistic, p_value, test_type = calculate_statistical_test(df, test_df, col)
                ks_dict_test[col] = {
                    'p_value': p_value,
                    'statistic': statistic,
                    'test_type': test_type
                }
        response['test_set'] = {
            'data': test_data_json,
            'num_rows': test_df.shape[0],
            'test_statistics': ks_dict_test
        }

    # Add iteration information to response
    if iteration_info:
        response['iteration_info'] = iteration_info

    # Clean up memory more aggressively
    try:
        del df, y, splits
        if test_df is not None:
            del test_df
        # Force garbage collection multiple times for better memory cleanup
        gc.collect()
        gc.collect()
    except:
        pass  # Ignore cleanup errors

    return response 