
import os
import sys
import uuid
import types
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
MODULE_DIR = BASE_DIR / "modules"

sys.path.insert(0, str(BASE_DIR))

if "modules" not in sys.modules:
    package = types.ModuleType("modules")
    package.__path__ = [str(MODULE_DIR)]
    package.__package__ = "modules"
    sys.modules["modules"] = package

import pandas as pd
from flask import Flask, render_template, request, redirect, url_for, flash, send_file

from modules.data_loader import load_dataset
from modules.data_quality import analyze_data
from modules.recommendations import generate_recommendations
from modules.dashboard import generate_dashboard
from modules.dashboard_exports import create_excel_report, create_pdf_report
from modules.ai_insights import answer_question
from modules.pattern_discovery import discover_patterns
from modules.data_cleaning import clean_data

app = Flask(__name__)
# Use a secure environment variable in production.
app.secret_key = os.environ.get("SECRET_KEY") or os.urandom(32)

# Maximum uploaded file size: 16 MB.
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024

UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

analysis_data = {}

@app.errorhandler(413)
def file_too_large(error):
    flash("File is too large. Maximum upload size is 16 MB.")
    return redirect(url_for("home")), 413


@app.route("/")
def home():
    return render_template("index.html")


def render_analysis(file_id):
    """Render an existing analysis using its stored dataset and results."""
    item = analysis_data.get(file_id)

    if not item:
        flash("This analysis session has expired. Please upload your dataset again.")
        return redirect(url_for("home"))

    df = item["df"]
    quality = analyze_data(df)

    return render_template(
        "index.html",
        file_id=file_id,
        filename=item["filename"],
        quality=quality,
        recommendations=generate_recommendations(quality),
        dashboard=generate_dashboard(df),
        patterns=discover_patterns(df),
        preview=df.head(10).to_html(
            classes="data-table", index=False, border=0
        ),
        answer=item.get("answer"),
        clean_summary=item.get("clean_summary"),
        cleaned_preview=item.get("cleaned_preview"),
        download_file=item.get("download_file")
    )


@app.route("/analysis/<file_id>", methods=["GET"])
def analysis(file_id):
    """Display an analysis through GET so browser refresh does not repeat POST."""
    return render_analysis(file_id)


@app.route("/upload", methods=["POST"])
def upload():
    file = request.files.get("file")

    if not file or not file.filename:
        flash("Please select a file.")
        return redirect(url_for("home"))

    extension = Path(file.filename).suffix.lower()
    if extension not in [".csv", ".xlsx", ".xls"]:
        flash("Only CSV and Excel files are supported.")
        return redirect(url_for("home"))

    file_id = uuid.uuid4().hex
    safe_name = file_id + extension
    path = UPLOAD_DIR / safe_name
    file.save(path)

    try:
        df = load_dataset(path)

        if df.empty:
            raise ValueError("The uploaded dataset is empty.")

        # Validate the main analysis before saving the session.
        quality = analyze_data(df)
        generate_recommendations(quality)
        generate_dashboard(df)
        discover_patterns(df)

        analysis_data[file_id] = {
            "df": df,
            "filename": file.filename
        }

        return redirect(url_for("analysis", file_id=file_id))

    except Exception as error:
        print(
            f"Upload analysis failed: {type(error).__name__}: {error}"
        )
        analysis_data.pop(file_id, None)
        path.unlink(missing_ok=True)

        flash(
            "Could not analyze this file. Please check that it is "
            "a valid, non-empty CSV or Excel file."
        )
        return redirect(url_for("home"))


@app.route("/ask", methods=["POST"])
def ask():
    file_id = request.form.get("file_id")
    question = request.form.get("question", "").strip()

    item = analysis_data.get(file_id)

    if not item:
        flash("Please upload your dataset again.")
        return redirect(url_for("home"))

    if not question:
        flash("Please enter a question for the AI assistant.")
        return redirect(url_for("analysis", file_id=file_id))

    try:
        item["answer"] = answer_question(item["df"], question)
    except Exception as error:
        print(f"AI question failed: {type(error).__name__}: {error}")
        flash("The AI assistant could not answer that question.")
    
    return redirect(url_for("analysis", file_id=file_id))


@app.route("/clean", methods=["POST"])
def clean():
    file_id = request.form.get("file_id")
    item = analysis_data.get(file_id)

    if not item:
        flash("Please upload your dataset again.")
        return redirect(url_for("home"))

    try:
        cleaned, summary = clean_data(
            item["df"],
            fill_missing=request.form.get("fill_missing") == "yes",
            remove_duplicates=request.form.get("remove_duplicates") == "yes",
            trim_text=request.form.get("trim_text") == "yes"
        )

        output_path = UPLOAD_DIR / f"cleaned_{file_id}.csv"
        cleaned.to_csv(output_path, index=False)

        item["clean_summary"] = summary
        item["cleaned_preview"] = cleaned.head(10).to_html(
            classes="data-table", index=False, border=0
        )
        item["download_file"] = output_path.name

    except Exception as error:
        print(f"Data cleaning failed: {type(error).__name__}: {error}")
        flash("Data cleaning failed. Please try again.")

    return redirect(url_for("analysis", file_id=file_id))


@app.route("/download/<filename>")
def download(filename):
    safe_path = (UPLOAD_DIR / filename).resolve()

    if safe_path.parent != UPLOAD_DIR.resolve() or not safe_path.is_file():
        return "File not found", 404

    return send_file(safe_path, as_attachment=True)



@app.route("/export/excel/<file_id>")
def export_excel(file_id):
    item = analysis_data.get(file_id)

    if not item:
        return "Dataset session expired. Please upload again.", 404

    output = create_excel_report(
        item["df"],
        item.get("filename", "dataset")
    )

    return send_file(
        output,
        as_attachment=True,
        download_name="DataDoctor_Dashboard.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


@app.route("/export/pdf/<file_id>")
def export_pdf(file_id):
    item = analysis_data.get(file_id)

    if not item:
        return "Dataset session expired. Please upload again.", 404

    output = create_pdf_report(
        item["df"],
        item.get("filename", "dataset")
    )

    return send_file(
        output,
        as_attachment=True,
        download_name="DataDoctor_Dashboard_Report.pdf",
        mimetype="application/pdf"
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=False)
