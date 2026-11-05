
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import html


# ---------------------------------------------------------
# DATA HELPERS
# ---------------------------------------------------------

def _find_column(df, possible_names):
    """Find a column using case-insensitive name matching."""
    lookup = {str(col).strip().lower(): col for col in df.columns}

    for name in possible_names:
        if name.lower() in lookup:
            return lookup[name.lower()]

    for col in df.columns:
        col_name = str(col).strip().lower()
        if any(name.lower() in col_name for name in possible_names):
            return col

    return None


def _format_number(value, currency=False):
    try:
        value = float(value)
        if currency:
            return f"${value:,.2f}"
        return f"{value:,.2f}"
    except (ValueError, TypeError):
        return str(value)


def _prepare_figure(fig, title):
    """Apply consistent readable styling to every chart."""
    fig.update_layout(
        title=dict(
            text=title,
            font=dict(size=21, color="#172033", family="Arial"),
            x=0.02,
            xanchor="left"
        ),
        height=440,
        autosize=True,
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#FFFFFF",
        font=dict(
            family="Arial, sans-serif",
            size=14,
            color="#202938"
        ),
        margin=dict(l=65, r=35, t=85, b=75),
        hoverlabel=dict(
            bgcolor="#172033",
            font_size=14,
            font_color="#FFFFFF"
        ),
        legend=dict(
            font=dict(size=13),
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )

    fig.update_xaxes(
        showgrid=False,
        showline=True,
        linecolor="#DCE2EA",
        tickfont=dict(size=12, color="#344054"),
        title_font=dict(size=14, color="#344054")
    )

    fig.update_yaxes(
        showgrid=True,
        gridcolor="#E9EDF3",
        zeroline=False,
        tickfont=dict(size=12, color="#344054"),
        title_font=dict(size=14, color="#344054")
    )

    return fig


def _chart_card(fig, title):
    """Convert a Plotly figure into a responsive chart card."""
    fig = _prepare_figure(fig, title)

    config = {
        "responsive": True,
        "displaylogo": False,
        "scrollZoom": True,
        "modeBarButtonsToRemove": ["lasso2d", "select2d"],
        "toImageButtonOptions": {
            "format": "png",
            "filename": "datadoctor_chart",
            "height": 900,
            "width": 1400,
            "scale": 2
        }
    }

    chart_html = fig.to_html(
        full_html=False,
        include_plotlyjs=False,
        config=config
    )

    return f"""
    <div class="dd-chart-card">
        <div class="dd-chart-heading">{html.escape(title)}</div>
        <div class="dd-chart-content">
            {chart_html}
        </div>
    </div>
    """


def _kpi_card(label, value, description):
    return f"""
    <div class="dd-kpi-card">
        <div class="dd-kpi-label">{html.escape(label)}</div>
        <div class="dd-kpi-value">{html.escape(str(value))}</div>
        <div class="dd-kpi-description">{html.escape(description)}</div>
    </div>
    """


# ---------------------------------------------------------
# MAIN DASHBOARD GENERATOR
# ---------------------------------------------------------

def generate_dashboard(df):

    if df is None or df.empty:
        return {
            "total_rows": 0,
            "total_columns": 0,
            "columns": [],
            "numeric_summary": {},
            "chart_html": "<p>No dataset available for visualization.</p>"
        }

    df = df.copy()

    total_rows = len(df)
    total_columns = len(df.columns)

    # Detect important business columns
    sales_col = _find_column(
        df, ["sales", "revenue", "amount", "total amount", "turnover"]
    )

    profit_col = _find_column(
        df, ["profit", "net profit", "earnings", "income"]
    )

    quantity_col = _find_column(
        df, ["quantity", "units sold", "units"]
    )

    order_col = _find_column(
        df, ["order id", "transaction id", "invoice id"]
    )

    category_col = _find_column(
        df, ["category", "product category", "type"]
    )

    region_col = _find_column(
        df, ["region", "area", "territory", "zone"]
    )

    date_col = _find_column(
        df, ["order date", "date", "transaction date", "created at"]
    )

    # Exclude identifiers from business numerical summaries
    numeric_cols = df.select_dtypes(include=np.number).columns.tolist()

    excluded_words = [
        "id", "postal", "zip", "code", "phone",
        "number", "index", "latitude", "longitude"
    ]

    business_numeric_cols = [
        col for col in numeric_cols
        if not any(word in str(col).lower() for word in excluded_words)
    ]

    numeric_summary = {}

    if business_numeric_cols:
        summary = df[business_numeric_cols].describe()

        for col in business_numeric_cols:
            numeric_summary[str(col)] = {
                str(index): round(float(value), 2)
                for index, value in summary[col].items()
                if pd.notna(value)
            }

    # -----------------------------------------------------
    # KPI CARDS
    # -----------------------------------------------------

    kpis = []

    if sales_col:
        sales_total = pd.to_numeric(
            df[sales_col], errors="coerce"
        ).sum()

        kpis.append(
            _kpi_card("Total Sales", _format_number(sales_total, True),
                      "Total recorded sales")
        )

    if profit_col:
        profit_total = pd.to_numeric(
            df[profit_col], errors="coerce"
        ).sum()

        kpis.append(
            _kpi_card("Total Profit", _format_number(profit_total, True),
                      "Total recorded profit")
        )

    if sales_col and profit_col:
        if sales_total != 0:
            margin = (profit_total / sales_total) * 100
        else:
            margin = 0

        kpis.append(
            _kpi_card("Profit Margin", f"{margin:.2f}%",
                      "Profit as a percentage of sales")
        )

    if order_col:
        orders = df[order_col].nunique()
        order_text = f"{orders:,}"
        order_description = "Unique orders"
    else:
        orders = total_rows
        order_text = f"{total_rows:,}"
        order_description = "Dataset records"

    kpis.append(
        _kpi_card("Total Orders", order_text, order_description)
    )

    # -----------------------------------------------------
    # CHART GENERATION
    # -----------------------------------------------------

    charts = []

    # 1. Monthly Sales Trend
    if sales_col and date_col:
        dates = pd.to_datetime(df[date_col], errors="coerce")
        sales_values = pd.to_numeric(df[sales_col], errors="coerce")

        monthly_df = pd.DataFrame({
            "Date": dates,
            "Sales": sales_values
        }).dropna()

        if not monthly_df.empty:
            monthly_df["Month"] = (
                monthly_df["Date"].dt.to_period("M").dt.to_timestamp()
            )

            monthly = (
                monthly_df.groupby("Month", as_index=False)["Sales"]
                .sum()
                .sort_values("Month")
            )

            fig = px.line(
                monthly,
                x="Month",
                y="Sales",
                markers=True,
                color_discrete_sequence=["#2563EB"]
            )

            fig.update_traces(
                line=dict(width=4),
                marker=dict(size=9),
                hovertemplate="Month: %{x|%b %Y}<br>Sales: %{y:,.2f}<extra></extra>"
            )

            fig.update_xaxes(title="Month")
            fig.update_yaxes(title="Sales")

            charts.append(_chart_card(fig, "Monthly Sales Trend"))

    # 2. Sales by Category
    if sales_col and category_col:
        category_data = df[[category_col, sales_col]].copy()
        category_data[sales_col] = pd.to_numeric(
            category_data[sales_col], errors="coerce"
        )

        category_data = (
            category_data.dropna()
            .groupby(category_col, as_index=False)[sales_col]
            .sum()
            .sort_values(sales_col, ascending=False)
            .head(12)
        )

        if not category_data.empty:
            fig = px.bar(
                category_data,
                x=category_col,
                y=sales_col,
                text_auto=".2s",
                color=sales_col,
                color_continuous_scale="Blues"
            )

            fig.update_traces(
                textposition="outside",
                hovertemplate="%{x}<br>Sales: %{y:,.2f}<extra></extra>"
            )

            fig.update_xaxes(title="Category")
            fig.update_yaxes(title="Total Sales")

            charts.append(_chart_card(fig, "Sales by Category"))

    # 3. Profit by Category
    if profit_col and category_col:
        profit_data = df[[category_col, profit_col]].copy()
        profit_data[profit_col] = pd.to_numeric(
            profit_data[profit_col], errors="coerce"
        )

        profit_data = (
            profit_data.dropna()
            .groupby(category_col, as_index=False)[profit_col]
            .sum()
            .sort_values(profit_col, ascending=True)
            .head(12)
        )

        if not profit_data.empty:
            fig = px.bar(
                profit_data,
                x=profit_col,
                y=category_col,
                orientation="h",
                text_auto=".2s",
                color=profit_col,
                color_continuous_scale="RdYlGn"
            )

            fig.update_traces(
                hovertemplate="%{y}<br>Profit: %{x:,.2f}<extra></extra>"
            )

            fig.update_xaxes(title="Total Profit")
            fig.update_yaxes(title="Category")

            charts.append(_chart_card(fig, "Profit by Category"))

    # 4. Sales by Region
    if sales_col and region_col:
        region_data = df[[region_col, sales_col]].copy()
        region_data[sales_col] = pd.to_numeric(
            region_data[sales_col], errors="coerce"
        )

        region_data = (
            region_data.dropna()
            .groupby(region_col, as_index=False)[sales_col]
            .sum()
            .sort_values(sales_col, ascending=False)
        )

        if not region_data.empty:
            fig = px.pie(
                region_data,
                names=region_col,
                values=sales_col,
                hole=0.48,
                color_discrete_sequence=px.colors.qualitative.Set2
            )

            fig.update_traces(
                textposition="inside",
                textinfo="percent+label",
                textfont_size=14,
                hovertemplate="%{label}<br>Sales: %{value:,.2f}<br>Share: %{percent}<extra></extra>"
            )

            charts.append(_chart_card(fig, "Sales Distribution by Region"))

    # 5. Sales vs Profit
    if sales_col and profit_col:
        scatter_df = df[[sales_col, profit_col]].copy()

        scatter_df[sales_col] = pd.to_numeric(
            scatter_df[sales_col], errors="coerce"
        )

        scatter_df[profit_col] = pd.to_numeric(
            scatter_df[profit_col], errors="coerce"
        )

        scatter_df = scatter_df.dropna()

        # Sample large datasets to keep the graph responsive
        if len(scatter_df) > 2500:
            scatter_df = scatter_df.sample(
                n=2500, random_state=42
            )

        if not scatter_df.empty:
            fig = px.scatter(
                scatter_df,
                x=sales_col,
                y=profit_col,
                opacity=0.65,
                color_discrete_sequence=["#2563EB"],
                render_mode="webgl"
            )

            fig.update_traces(
                marker=dict(size=8),
                hovertemplate="Sales: %{x:,.2f}<br>Profit: %{y:,.2f}<extra></extra>"
            )

            fig.update_xaxes(title="Sales")
            fig.update_yaxes(title="Profit")

            charts.append(_chart_card(fig, "Sales vs Profit Relationship"))

    # 6. Quantity by Category
    if quantity_col and category_col:
        quantity_data = df[[category_col, quantity_col]].copy()
        quantity_data[quantity_col] = pd.to_numeric(
            quantity_data[quantity_col], errors="coerce"
        )

        quantity_data = (
            quantity_data.dropna()
            .groupby(category_col, as_index=False)[quantity_col]
            .sum()
            .sort_values(quantity_col, ascending=False)
            .head(12)
        )

        if not quantity_data.empty:
            fig = px.bar(
                quantity_data,
                x=category_col,
                y=quantity_col,
                text_auto=".2s",
                color_discrete_sequence=["#0F9D8A"]
            )

            fig.update_traces(
                textposition="outside",
                hovertemplate="%{x}<br>Quantity: %{y:,.0f}<extra></extra>"
            )

            fig.update_xaxes(title="Category")
            fig.update_yaxes(title="Quantity Sold")

            charts.append(_chart_card(fig, "Quantity by Category"))

    # -----------------------------------------------------
    # GENERIC FALLBACK CHARTS
    # -----------------------------------------------------

    if not charts:
        if business_numeric_cols:
            col = business_numeric_cols[0]

            values = pd.to_numeric(
                df[col], errors="coerce"
            ).dropna()

            if not values.empty:
                fig = px.histogram(
                    values,
                    x=col,
                    nbins=30,
                    color_discrete_sequence=["#2563EB"]
                )

                fig.update_xaxes(title=str(col))
                fig.update_yaxes(title="Frequency")

                charts.append(
                    _chart_card(fig, f"Distribution of {col}")
                )

        categorical_cols = df.select_dtypes(
            include=["object", "category"]
        ).columns.tolist()

        if categorical_cols:
            col = categorical_cols[0]
            counts = df[col].astype(str).value_counts().head(12)

            if not counts.empty:
                fig = px.bar(
                    x=counts.index,
                    y=counts.values,
                    labels={"x": str(col), "y": "Records"},
                    color_discrete_sequence=["#0F9D8A"]
                )

                fig.update_xaxes(title=str(col))
                fig.update_yaxes(title="Number of Records")

                charts.append(
                    _chart_card(fig, f"Top Values in {col}")
                )

    if charts:
        chart_section = "\n".join(charts)
    else:
        chart_section = """
        <div class="dd-empty-chart">
            Not enough suitable data was found to generate charts.
        </div>
        """

    kpi_section = "\n".join(kpis)

    chart_html = f"""
    <div class="dd-dashboard">
        <div class="dd-dashboard-intro">
            <div>
                <div class="dd-dashboard-eyebrow">BUSINESS INTELLIGENCE</div>
                <h2>Dataset Performance Overview</h2>
                <p>Key metrics and interactive visual analysis of your dataset.</p>
            </div>
            <div class="dd-dataset-count">
                {total_rows:,} records · {total_columns} columns
            </div>
        </div>

        <div class="dd-kpi-grid">
            {kpi_section}
        </div>

        <div class="dd-chart-grid">
            {chart_section}
        </div>
    </div>
    """

    return {
        "total_rows": total_rows,
        "total_columns": total_columns,
        "columns": list(df.columns),
        "numeric_summary": numeric_summary,
        "chart_html": chart_html
    }
