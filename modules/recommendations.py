
def generate_recommendations(report):
    recommendations = []

    if report["total_missing"] > 0:
        recommendations.append(
            "Missing values detected. Consider filling or reviewing them."
        )

    if report["duplicate_rows"] > 0:
        recommendations.append(
            "Duplicate rows detected. Review them before removing."
        )

    if any(count > 0 for count in report["outliers"].values()):
        recommendations.append(
            "Numerical outliers detected. Investigate unusual values."
        )

    if not recommendations:
        recommendations.append(
            "Great! No major data-quality issues were detected."
        )

    return recommendations
