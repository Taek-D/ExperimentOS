import pandas as pd
from .schema import IntegrationResult

def to_experiment_df(result: IntegrationResult) -> pd.DataFrame:
    """
    Converts an IntegrationResult into a pandas DataFrame compatible with
    the existing analysis pipeline.
    
    Args:
        result: Validated IntegrationResult object.
        
    Returns:
        pd.DataFrame: DataFrame with columns 'variant', 'users', 'conversions',
                      and any additional metrics found in the first variant.
    """
    data = []
    
    # Collect all potential metric keys from all variants to ensure schema consistency
    all_metric_keys: set[str] = set()
    for variant in result.variants:
        if variant.metrics:
            all_metric_keys.update(variant.metrics.keys())
            
    for variant in result.variants:
        row = {
            "variant": variant.name,
            "users": variant.users,
            "conversions": variant.conversions
        }
        
        # Always fill metric keys, using 0 as default if missing or metrics is empty
        # Pydantic schema ensures metrics is at least empty dict, never None (default_factory=dict)
        metrics = variant.metrics or {} 
        for key in all_metric_keys:
            row[key] = metrics.get(key, 0)
                
        data.append(row)
        
    df = pd.DataFrame(data)
    
    # Ensure column types are correct
    df["users"] = df["users"].astype(int)
    df["conversions"] = df["conversions"].astype(int)
    
    # Normalize variant names to lowercase standard if "control" is present
    
    def standardize_name(name):
        lower_name = name.lower()
        if lower_name == "control":
            return "control"
        if lower_name == "treatment":
            return "treatment"
        return name

    df["variant"] = df["variant"].apply(standardize_name)
    
    return df
