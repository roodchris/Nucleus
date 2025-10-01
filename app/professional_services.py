from flask import Blueprint, render_template

professional_services_bp = Blueprint('professional_services', __name__, url_prefix='/professional-services')

@professional_services_bp.route('/')
def professional_services():
    """Professional Services overview page"""
    return render_template('professional_services/index.html')

@professional_services_bp.route('/tax-optimization')
def tax_optimization():
    """Tax Optimization service page"""
    return render_template('professional_services/tax_optimization.html')

@professional_services_bp.route('/contract-negotiation')
def contract_negotiation():
    """Contract Negotiation service page"""
    return render_template('professional_services/contract_negotiation.html')

@professional_services_bp.route('/personalized-recruiting')
def personalized_recruiting():
    """Personalized Recruiting service page"""
    return render_template('professional_services/personalized_recruiting.html')

@professional_services_bp.route('/starting-practice')
def starting_practice():
    """Starting Your Own Practice service page"""
    return render_template('professional_services/starting_practice.html')

