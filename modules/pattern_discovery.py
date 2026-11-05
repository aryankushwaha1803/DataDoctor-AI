
def discover_patterns(df):
    numeric_df = df.select_dtypes(include="number")

    if numeric_df.shape[1] < 2:
        return {
            "message": "At least two numerical columns are required to discover correlations.",
            "correlations": {}
        }

    correlations = numeric_df.corr().round(2).to_dict()

    return {
        "message": "Correlation analysis completed successfully.",
        "correlations": correlations
    }
