from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from .models import db
from .wrvu_data import WRVU_DATA
import json

wrvu_bp = Blueprint("wrvu_calculator", __name__)

@wrvu_bp.route("/wrvu-calculator")
@login_required
def calculator():
    """Main wRVU calculator page"""
    return render_template("wrvu_calculator/index.html", wrvu_data=WRVU_DATA)

@wrvu_bp.route("/api/wrvu-data")
@login_required
def get_wrvu_data():
    """API endpoint to get wRVU data"""
    return jsonify(WRVU_DATA)

@wrvu_bp.route("/api/calculate-revenue", methods=["POST"])
@login_required
def calculate_revenue():
    """API endpoint to calculate revenue based on selected studies and compensation rate"""
    try:
        data = request.get_json()
        compensation_rate = float(data.get('compensation_rate', 0))
        selected_studies = data.get('selected_studies', [])
        
        total_studies = len(selected_studies)
        total_wrvus = sum(WRVU_DATA.get(study, {}).get('wrvu', 0) for study in selected_studies)
        expected_revenue = total_wrvus * compensation_rate
        
        return jsonify({
            'total_studies': total_studies,
            'total_wrvus': round(total_wrvus, 1),
            'expected_revenue': round(expected_revenue, 2)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400
