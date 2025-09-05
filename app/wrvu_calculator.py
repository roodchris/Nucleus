from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from .models import db, ShiftSession, RVURecord
from .wrvu_data import WRVU_DATA
from datetime import datetime, date, timedelta
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


@wrvu_bp.route("/api/start-shift", methods=["POST"])
@login_required
def start_shift():
    """Start a new shift session"""
    try:
        data = request.get_json()
        compensation_rate = float(data.get('compensation_rate', 0))
        
        # Check if there's an active shift
        active_shift = ShiftSession.query.filter_by(
            user_id=current_user.id, 
            is_active=True
        ).first()
        
        if active_shift:
            return jsonify({'error': 'You already have an active shift'}), 400
        
        # Create new shift session
        shift = ShiftSession(
            user_id=current_user.id,
            start_time=datetime.utcnow(),
            compensation_rate=compensation_rate
        )
        
        db.session.add(shift)
        db.session.commit()
        
        return jsonify({
            'shift_id': shift.id,
            'start_time': shift.start_time.isoformat(),
            'total_rvus': shift.total_rvus,
            'total_revenue': shift.total_revenue,
            'compensation_rate': shift.compensation_rate,
            'message': 'Shift started successfully'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@wrvu_bp.route("/api/end-shift", methods=["POST"])
@login_required
def end_shift():
    """End the current active shift session"""
    try:
        # Find active shift
        active_shift = ShiftSession.query.filter_by(
            user_id=current_user.id, 
            is_active=True
        ).first()
        
        if not active_shift:
            return jsonify({'error': 'No active shift found'}), 400
        
        # Calculate totals
        total_rvus = sum(record.wrvu_value for record in active_shift.rvu_records)
        total_revenue = total_rvus * active_shift.compensation_rate
        
        # Update shift
        active_shift.end_time = datetime.utcnow()
        active_shift.total_rvus = total_rvus
        active_shift.total_revenue = total_revenue
        active_shift.is_active = False
        
        db.session.commit()
        
        return jsonify({
            'shift_id': active_shift.id,
            'end_time': active_shift.end_time.isoformat(),
            'total_rvus': total_rvus,
            'total_revenue': total_revenue,
            'message': 'Shift ended successfully'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@wrvu_bp.route("/api/add-rvu", methods=["POST"])
@login_required
def add_rvu():
    """Add an RVU record to the current active shift"""
    try:
        data = request.get_json()
        study_name = data.get('study_name')
        wrvu_value = float(data.get('wrvu_value', 0))
        
        # Find active shift
        active_shift = ShiftSession.query.filter_by(
            user_id=current_user.id, 
            is_active=True
        ).first()
        
        if not active_shift:
            return jsonify({'error': 'No active shift found'}), 400
        
        # Create RVU record
        rvu_record = RVURecord(
            shift_session_id=active_shift.id,
            study_name=study_name,
            wrvu_value=wrvu_value
        )
        
        db.session.add(rvu_record)
        db.session.commit()
        
        # Calculate new totals
        total_rvus = sum(record.wrvu_value for record in active_shift.rvu_records)
        total_revenue = total_rvus * active_shift.compensation_rate
        
        return jsonify({
            'record_id': rvu_record.id,
            'total_rvus': total_rvus,
            'total_revenue': total_revenue,
            'message': 'RVU record added successfully'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@wrvu_bp.route("/api/active-shift")
@login_required
def get_active_shift():
    """Get current active shift information"""
    try:
        active_shift = ShiftSession.query.filter_by(
            user_id=current_user.id, 
            is_active=True
        ).first()
        
        if not active_shift:
            return jsonify({'active': False})
        
        # Get RVU records for this shift
        rvu_records = [
            {
                'id': record.id,
                'study_name': record.study_name,
                'wrvu_value': record.wrvu_value,
                'recorded_at': record.recorded_at.isoformat()
            }
            for record in active_shift.rvu_records
        ]
        
        total_rvus = sum(record.wrvu_value for record in active_shift.rvu_records)
        total_revenue = total_rvus * active_shift.compensation_rate
        
        return jsonify({
            'active': True,
            'shift_id': active_shift.id,
            'start_time': active_shift.start_time.isoformat(),
            'compensation_rate': active_shift.compensation_rate,
            'total_rvus': total_rvus,
            'total_revenue': total_revenue,
            'rvu_records': rvu_records
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@wrvu_bp.route("/api/shift-calendar")
@login_required
def get_shift_calendar():
    """Get shift data for calendar display"""
    try:
        # Get all completed shifts for the user
        shifts = ShiftSession.query.filter_by(
            user_id=current_user.id,
            is_active=False
        ).order_by(ShiftSession.start_time.desc()).all()
        
        calendar_data = {}
        for shift in shifts:
            # Convert UTC time to local timezone for date calculation
            # Assume user is in Eastern Time (UTC-4 for EDT) for now
            local_offset_hours = -4
            local_time = shift.start_time + timedelta(hours=local_offset_hours)
            shift_date = local_time.date().isoformat()
            
            if shift_date not in calendar_data:
                calendar_data[shift_date] = {
                    'total_rvus': 0,
                    'total_revenue': 0,
                    'shifts': []
                }
            
            calendar_data[shift_date]['total_rvus'] += shift.total_rvus
            calendar_data[shift_date]['total_revenue'] += shift.total_revenue
            calendar_data[shift_date]['shifts'].append({
                'id': shift.id,
                'start_time': shift.start_time.isoformat(),
                'end_time': shift.end_time.isoformat() if shift.end_time else None,
                'total_rvus': shift.total_rvus,
                'total_revenue': shift.total_revenue,
                'compensation_rate': shift.compensation_rate
            })
        
        return jsonify(calendar_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@wrvu_bp.route("/api/shift-details/<int:shift_id>")
@login_required
def get_shift_details(shift_id):
    """Get detailed RVU records for a specific shift"""
    try:
        shift = ShiftSession.query.filter_by(
            id=shift_id,
            user_id=current_user.id
        ).first()
        
        if not shift:
            return jsonify({'error': 'Shift not found'}), 404
        
        rvu_records = [
            {
                'id': record.id,
                'study_name': record.study_name,
                'wrvu_value': record.wrvu_value,
                'recorded_at': record.recorded_at.isoformat()
            }
            for record in shift.rvu_records
        ]
        
        return jsonify({
            'shift_id': shift.id,
            'start_time': shift.start_time.isoformat(),
            'end_time': shift.end_time.isoformat() if shift.end_time else None,
            'total_rvus': shift.total_rvus,
            'total_revenue': shift.total_revenue,
            'compensation_rate': shift.compensation_rate,
            'rvu_records': rvu_records
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400
