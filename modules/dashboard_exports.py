
from io import BytesIO
import pandas as pd


def find_column(df, names):
    lookup = {str(c).strip().lower(): c for c in df.columns}

    for name in names:
        if name.lower() in lookup:
            return lookup[name.lower()]

    for col in df.columns:
        if any(name.lower() in str(col).lower() for name in names):
            return col

    return None


def get_kpis(df):
    sales = find_column(df, ["sales", "revenue", "amount", "turnover"])
    profit = find_column(df, ["profit", "earnings", "income"])
    quantity = find_column(df, ["quantity", "units sold", "units"])
    order = find_column(df, ["order id", "transaction id", "invoice id"])

    result = [
        ("Total Records", f"{len(df):,}"),
        ("Total Columns", f"{len(df.columns):,}")
    ]

    sales_total = None
    profit_total = None

    if sales:
        sales_total = pd.to_numeric(
            df[sales], errors="coerce"
        ).sum()
        result.append(("Total Sales", f"{sales_total:,.2f}"))

    if profit:
        profit_total = pd.to_numeric(
            df[profit], errors="coerce"
        ).sum()
        result.append(("Total Profit", f"{profit_total:,.2f}"))

    if sales and profit and sales_total:
        result.append((
            "Profit Margin",
            f"{(profit_total / sales_total) * 100:.2f}%"
        ))

    if quantity:
        total_quantity = pd.to_numeric(
            df[quantity], errors="coerce"
        ).sum()
        result.append(("Total Quantity", f"{total_quantity:,.0f}"))

    if order:
        result.append(("Unique Orders", f"{df[order].nunique():,}"))

    return result


def create_excel_report(df, original_filename="dataset"):
    output = BytesIO()
    kpis = get_kpis(df)

    with pd.ExcelWriter(output, engine="openpyxl") as writer:

        df.to_excel(
            writer,
            sheet_name="Dataset",
            index=False
        )

        pd.DataFrame(
            kpis,
            columns=["KPI", "Value"]
        ).to_excel(
            writer,
            sheet_name="Dashboard KPIs",
            index=False
        )

        numeric = df.select_dtypes(include="number")

        if not numeric.empty:
            numeric.describe().round(2).to_excel(
                writer,
                sheet_name="Numeric Summary"
            )

        quality = pd.DataFrame({
            "Metric": [
                "Total Rows",
                "Total Columns",
                "Missing Cells",
                "Duplicate Rows"
            ],
            "Value": [
                len(df),
                len(df.columns),
                int(df.isna().sum().sum()),
                int(df.duplicated().sum())
            ]
        })

        quality.to_excel(
            writer,
            sheet_name="Data Quality",
            index=False
        )

        for ws in writer.book.worksheets:
            ws.freeze_panes = "A2"
            ws.auto_filter.ref = ws.dimensions

            for column_cells in ws.columns:
                letter = column_cells[0].column_letter
                max_length = max(
                    len(str(cell.value or ""))
                    for cell in column_cells
                )
                ws.column_dimensions[letter].width = min(
                    max(max_length + 3, 12), 35
                )

    output.seek(0)
    return output


def create_pdf_report(df, original_filename="dataset"):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table,
        TableStyle, Image, PageBreak
    )

    output = BytesIO()
    page_size = landscape(A4)

    doc = SimpleDocTemplate(
        output,
        pagesize=page_size,
        rightMargin=15 * mm,
        leftMargin=15 * mm,
        topMargin=15 * mm,
        bottomMargin=15 * mm
    )

    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph(
        "DataDoctor AI — Dataset Dashboard Report",
        styles["Title"]
    ))

    story.append(Spacer(1, 5 * mm))

    story.append(Paragraph(
        f"Dataset: {str(original_filename)}",
        styles["Normal"]
    ))

    story.append(Paragraph(
        f"Generated: {pd.Timestamp.now().strftime('%d %b %Y, %I:%M %p')}",
        styles["Normal"]
    ))

    story.append(Spacer(1, 6 * mm))

    # KPI TABLE
    story.append(Paragraph(
        "Key Performance Indicators",
        styles["Heading2"]
    ))

    kpi_data = [["Metric", "Value"]]
    kpi_data.extend([
        [str(k), str(v)] for k, v in get_kpis(df)
    ])

    kpi_table = Table(
        kpi_data,
        colWidths=[65 * mm, 65 * mm],
        repeatRows=1
    )

    kpi_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#172554")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#dbe3ee")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1),
         [colors.white, colors.HexColor("#f1f5f9")]),
        ("PADDING", (0, 0), (-1, -1), 7)
    ]))

    story.append(kpi_table)
    story.append(Spacer(1, 6 * mm))

    # DATA QUALITY TABLE
    story.append(Paragraph(
        "Data Quality Summary",
        styles["Heading2"]
    ))

    quality_data = [
        ["Quality Check", "Result"],
        ["Missing Cells", f"{int(df.isna().sum().sum()):,}"],
        ["Duplicate Rows", f"{int(df.duplicated().sum()):,}"],
        ["Total Rows", f"{len(df):,}"],
        ["Total Columns", f"{len(df.columns):,}"]
    ]

    quality_table = Table(
        quality_data,
        colWidths=[65 * mm, 65 * mm]
    )

    quality_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f766e")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#dbe3ee")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1),
         [colors.white, colors.HexColor("#f1f5f9")]),
        ("PADDING", (0, 0), (-1, -1), 7)
    ]))

    story.append(quality_table)

    # DETECT CHART COLUMNS
    sales_col = find_column(
        df, ["sales", "revenue", "amount", "turnover"]
    )
    profit_col = find_column(
        df, ["profit", "earnings", "income"]
    )
    category_col = find_column(
        df, ["category", "product category"]
    )
    region_col = find_column(
        df, ["region", "territory", "zone"]
    )
    date_col = find_column(
        df, ["order date", "transaction date", "date"]
    )
    quantity_col = find_column(
        df, ["quantity", "units sold", "units"]
    )

    chart_images = []

    def add_bar_chart(group_col, metric_col, title):
        if not group_col or not metric_col:
            return

        temp = df[[group_col, metric_col]].copy()
        temp[metric_col] = pd.to_numeric(
            temp[metric_col], errors="coerce"
        )

        grouped = (
            temp.dropna()
            .groupby(group_col)[metric_col]
            .sum()
            .sort_values(ascending=False)
            .head(10)
        )

        if grouped.empty:
            return

        fig, ax = plt.subplots(figsize=(8, 3.5))
        grouped.sort_values().plot(kind="barh", ax=ax)

        ax.set_title(title)
        ax.set_xlabel(str(metric_col))
        ax.set_ylabel(str(group_col))
        ax.grid(axis="x", alpha=0.2)

        fig.tight_layout()

        chart_buffer = BytesIO()
        fig.savefig(
            chart_buffer,
            format="png",
            dpi=150,
            bbox_inches="tight"
        )

        plt.close(fig)
        chart_buffer.seek(0)

        chart_images.append(
            Image(chart_buffer, width=115 * mm, height=52 * mm)
        )

    if sales_col and category_col:
        add_bar_chart(
            category_col, sales_col, "Sales by Category"
        )

    if profit_col and category_col:
        add_bar_chart(
            category_col, profit_col, "Profit by Category"
        )

    # SALES DISTRIBUTION BY REGION - PIE CHART
    if sales_col and region_col:
        temp = df[[region_col, sales_col]].copy()
        temp[sales_col] = pd.to_numeric(
            temp[sales_col], errors="coerce"
        )
        grouped = (
            temp.dropna()
            .groupby(region_col)[sales_col]
            .sum()
            .sort_values(ascending=False)
        )

        if not grouped.empty:
            fig, ax = plt.subplots(figsize=(8, 5))
            ax.pie(
                grouped.values,
                labels=grouped.index.astype(str),
                autopct="%1.1f%%",
                startangle=90,
                wedgeprops={"width": 0.48}
            )
            ax.set_title("Sales Distribution by Region")
            ax.axis("equal")
            fig.tight_layout()

            buf = BytesIO()
            fig.savefig(buf, format="png", dpi=180,
                        bbox_inches="tight")
            plt.close(fig)
            buf.seek(0)
            chart_images.append(
                Image(buf, width=115 * mm, height=70 * mm)
            )

    # SALES VS PROFIT RELATIONSHIP - SCATTER CHART
    if sales_col and profit_col:
        temp = df[[sales_col, profit_col]].copy()
        temp[sales_col] = pd.to_numeric(
            temp[sales_col], errors="coerce"
        )
        temp[profit_col] = pd.to_numeric(
            temp[profit_col], errors="coerce"
        )
        temp = temp.dropna()

        if len(temp) > 2500:
            temp = temp.sample(2500, random_state=42)

        if not temp.empty:
            fig, ax = plt.subplots(figsize=(8, 4.5))
            ax.scatter(
                temp[sales_col], temp[profit_col],
                alpha=0.65, s=24
            )
            ax.set_title("Sales vs Profit Relationship")
            ax.set_xlabel(str(sales_col))
            ax.set_ylabel(str(profit_col))
            ax.grid(alpha=0.2)
            fig.tight_layout()

            buf = BytesIO()
            fig.savefig(buf, format="png", dpi=180,
                        bbox_inches="tight")
            plt.close(fig)
            buf.seek(0)
            chart_images.append(
                Image(buf, width=115 * mm, height=65 * mm)
            )

    # QUANTITY BY CATEGORY
    if quantity_col and category_col:
        temp = df[[category_col, quantity_col]].copy()
        temp[quantity_col] = pd.to_numeric(
            temp[quantity_col], errors="coerce"
        )
        grouped = (
            temp.dropna()
            .groupby(category_col)[quantity_col]
            .sum()
            .sort_values(ascending=False)
            .head(12)
        )

        if not grouped.empty:
            fig, ax = plt.subplots(figsize=(8, 4.5))
            grouped.sort_values().plot(
                kind="barh", ax=ax
            )
            ax.set_title("Quantity by Category")
            ax.set_xlabel("Quantity Sold")
            ax.set_ylabel("Category")
            ax.grid(axis="x", alpha=0.2)
            fig.tight_layout()

            buf = BytesIO()
            fig.savefig(buf, format="png", dpi=180,
                        bbox_inches="tight")
            plt.close(fig)
            buf.seek(0)
            chart_images.append(
                Image(buf, width=115 * mm, height=65 * mm)
            )

    # MONTHLY SALES TREND
    if sales_col and date_col:
        dates = pd.to_datetime(
            df[date_col], errors="coerce"
        )
        amounts = pd.to_numeric(
            df[sales_col], errors="coerce"
        )

        temp = pd.DataFrame({
            "Date": dates,
            "Sales": amounts
        }).dropna()

        if not temp.empty:
            temp["Month"] = (
                temp["Date"].dt.to_period("M").astype(str)
            )

            monthly = (
                temp.groupby("Month")["Sales"]
                .sum()
                .sort_index()
            )

            fig, ax = plt.subplots(figsize=(8, 3.5))
            monthly.plot(kind="line", marker="o", ax=ax)

            ax.set_title("Monthly Sales Trend")
            ax.set_xlabel("Month")
            ax.set_ylabel("Sales")
            ax.tick_params(axis="x", rotation=35)
            ax.grid(alpha=0.2)

            fig.tight_layout()

            chart_buffer = BytesIO()
            fig.savefig(
                chart_buffer,
                format="png",
                dpi=150,
                bbox_inches="tight"
            )

            plt.close(fig)
            chart_buffer.seek(0)

            chart_images.append(
                Image(chart_buffer, width=115 * mm, height=52 * mm)
            )

    if chart_images:
        story.append(PageBreak())
        story.append(Paragraph(
            "Dashboard Charts",
            styles["Heading2"]
        ))
        story.append(Spacer(1, 4 * mm))

        for index, chart in enumerate(chart_images):
            if index > 0:
                story.append(PageBreak())
            story.append(chart)

    # DATA PREVIEW
    story.append(PageBreak())
    story.append(Paragraph(
        "Dataset Preview — First 25 Rows",
        styles["Heading2"]
    ))

    preview = df.head(25).copy().fillna("")
    headers = [str(c)[:24] for c in preview.columns]

    table_data = [headers]

    for _, row in preview.iterrows():
        table_data.append([
            str(v)[:35] for v in row.tolist()
        ])

    available_width = page_size[0] - 30 * mm
    col_width = available_width / max(len(headers), 1)

    preview_table = Table(
        table_data,
        colWidths=[col_width] * len(headers),
        repeatRows=1
    )

    preview_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#172554")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 6),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#cbd5e1")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1),
         [colors.white, colors.HexColor("#f8fafc")]),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("PADDING", (0, 0), (-1, -1), 3)
    ]))

    story.append(preview_table)

    doc.build(story)
    output.seek(0)

    return output
