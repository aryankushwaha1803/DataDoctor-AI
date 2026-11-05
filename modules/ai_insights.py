
import pandas as pd
import re

def normalize(text):
    return re.sub(r"[^a-z0-9]+", "_", str(text).lower()).strip("_")

def find_column(df, aliases):
    normalized = {normalize(c): c for c in df.columns}

    for alias in aliases:
        key = normalize(alias)
        if key in normalized:
            return normalized[key]

    for key, original in normalized.items():
        if any(normalize(alias) in key for alias in aliases):
            return original

    return None

def money(value):
    return "₹{:,.2f}".format(float(value))

def answer_question(df, question):
    if df is None or df.empty:
        return "Please upload a dataset containing records first."

    q = question.lower().strip()
    if not q:
        return "Please enter a question about your dataset."

    rows = len(df)
    columns = len(df.columns)
    numeric = df.select_dtypes(include="number")

    sales_col = find_column(df, [
        "Sales_INR", "Sales", "Revenue", "Total Sales", "Amount"
    ])
    profit_col = find_column(df, [
        "Profit_INR", "Profit", "Net Profit", "Earnings"
    ])
    quantity_col = find_column(df, ["Quantity", "Units Sold"])
    order_col = find_column(df, ["Order_ID", "Order ID", "Invoice"])

    product_col = find_column(df, ["Product", "Product Name", "Item"])
    category_col = find_column(df, ["Category", "Product Category"])
    region_col = find_column(df, ["Region", "Area", "Location", "State"])
    date_col = find_column(df, ["Order_Date", "Date", "Transaction Date"])

    # Basic dataset questions
    if any(x in q for x in ["how many rows", "number of rows", "total rows", "row count"]):
        return f"Your dataset contains {rows:,} rows."

    if any(x in q for x in ["how many columns", "number of columns", "total columns", "column count"]):
        return f"Your dataset contains {columns} columns: {', '.join(map(str, df.columns))}."

    if "column" in q and ("name" in q or "list" in q):
        return "Dataset columns: " + ", ".join(map(str, df.columns))

    if "missing" in q or "null" in q or "empty value" in q:
        total = int(df.isnull().sum().sum())
        details = df.isnull().sum()
        affected = details[details > 0].to_dict()
        if not total:
            return "Excellent! Your dataset contains no missing values."
        return f"Your dataset contains {total} missing cells. Affected columns: {affected}"

    if "duplicate" in q:
        count = int(df.duplicated().sum())
        return f"Your dataset contains {count} duplicate rows."

    if "average" in q or "mean" in q:
        if numeric.empty:
            return "No numerical columns were found."
        averages = numeric.mean().round(2).to_dict()
        return "Average values by numerical column:\n" + str(averages)

    # Total orders
    if "order" in q and any(x in q for x in ["total", "number", "how many", "count"]):
        count = df[order_col].nunique() if order_col else rows
        return f"Total orders: {count:,}."

    # Total sales
    if sales_col and any(x in q for x in [
        "total sales", "sales generated", "total revenue",
        "revenue generated", "sales amount", "how much sales"
    ]):
        return f"Total sales/revenue: {money(df[sales_col].sum())}."

    # Total profit
    if profit_col and any(x in q for x in [
        "total profit", "profit generated", "net profit",
        "how much profit", "total earnings"
    ]):
        return f"Total profit: {money(df[profit_col].sum())}."

    # Profit margin
    if "margin" in q or "profitability" in q:
        if profit_col and sales_col:
            sales = df[sales_col].sum()
            profit = df[profit_col].sum()
            margin = (profit / sales * 100) if sales else 0
            return f"Overall profit margin: {margin:.2f}% (total profit divided by total sales)."
        return "I need both a sales/revenue column and a profit column to calculate profit margin."

    # Quantity
    if quantity_col and ("quantity" in q or "units sold" in q):
        if any(x in q for x in ["total", "sum", "sold"]):
            return f"Total quantity sold: {df[quantity_col].sum():,.0f}."
        return f"Average quantity: {df[quantity_col].mean():.2f}."

    # Determine the metric for grouped analysis
    if "profit" in q or "earning" in q:
        metric = profit_col
    elif "sales" in q or "revenue" in q:
        metric = sales_col
    elif "quantity" in q or "units" in q:
        metric = quantity_col
    else:
        metric = None

    # Determine grouping column
    if "region" in q or "state" in q or "location" in q:
        group_col = region_col
    elif "category" in q:
        group_col = category_col
    elif "product" in q or "item" in q:
        group_col = product_col
    else:
        group_col = None

    # Highest / lowest product, category or region
    if group_col and metric and any(x in q for x in [
        "highest", "top", "best", "maximum", "most", "lowest", "least"
    ]):
        grouped = df.groupby(group_col)[metric].sum().sort_values(
            ascending=any(x in q for x in ["lowest", "least"])
        )
        if grouped.empty:
            return "There is not enough data for this comparison."

        name = grouped.index[0]
        value = grouped.iloc[0]
        label = "lowest" if any(x in q for x in ["lowest", "least"]) else "highest"
        formatted = money(value) if metric in [sales_col, profit_col] else f"{value:,.2f}"
        return f"The {label} {group_col} by {metric} is {name}, with {formatted}."

    # Show top 5
    if group_col and metric and ("top 5" in q or "top five" in q):
        result = df.groupby(group_col)[metric].sum().nlargest(5)
        return "Top 5 results:\n" + "\n".join(
            f"{i+1}. {name}: {money(value) if metric in [sales_col, profit_col] else round(value, 2)}"
            for i, (name, value) in enumerate(result.items())
        )

    # Correlation
    if "correlation" in q or "correlated" in q or "relationship" in q:
        if numeric.shape[1] < 2:
            return "At least two numerical columns are needed for correlation analysis."
        corr = numeric.corr().round(2)
        return "Correlation matrix:\n" + corr.to_string()

    # Date-based trend
    if date_col and any(x in q for x in ["monthly", "month", "trend", "over time"]):
        if not metric:
            metric = sales_col or profit_col
        if metric:
            dates = pd.to_datetime(df[date_col], errors="coerce")
            valid = df.assign(_date=dates).dropna(subset=["_date"])
            if not valid.empty:
                monthly = valid.groupby(valid["_date"].dt.to_period("M"))[metric].sum()
                return "Monthly trend:\n" + "\n".join(
                    f"{period}: {money(value) if metric in [sales_col, profit_col] else round(value, 2)}"
                    for period, value in monthly.items()
                )

    # General numeric column query
    for col in numeric.columns:
        if normalize(col) in normalize(q):
            return (
                f"{col} summary:\n"
                f"Total: {numeric[col].sum():,.2f}\n"
                f"Average: {numeric[col].mean():,.2f}\n"
                f"Minimum: {numeric[col].min():,.2f}\n"
                f"Maximum: {numeric[col].max():,.2f}"
            )

    return (
        "I couldn't identify that question yet. Try asking:\n"
        "- What is the total sales?\n"
        "- What is the total profit?\n"
        "- Which product has the highest sales?\n"
        "- Which category generates the highest profit?\n"
        "- Which region has the highest sales?\n"
        "- What is the profit margin?\n"
        "- Show monthly sales trends.\n"
        "- How many missing values are there?"
    )
