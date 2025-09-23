from flask import Blueprint, Response, url_for
from app.models import Opportunity, ForumPost, ProgramReview, JobReview
from datetime import datetime
import xml.etree.ElementTree as ET

sitemap_bp = Blueprint('sitemap', __name__)

@sitemap_bp.route('/sitemap.xml')
def sitemap():
    """Generate XML sitemap for SEO"""
    urlset = ET.Element('urlset')
    urlset.set('xmlns', 'http://www.sitemaps.org/schemas/sitemap/0.9')
    urlset.set('xmlns:xsi', 'http://www.w3.org/2001/XMLSchema-instance')
    urlset.set('xsi:schemaLocation', 'http://www.sitemaps.org/schemas/sitemap/0.9 http://www.sitemaps.org/schemas/sitemap/0.9/sitemap.xsd')

    # Static pages
    static_pages = [
        ('/', '1.0', 'daily'),
        ('/opportunities', '0.9', 'daily'),
        ('/forum', '0.8', 'daily'),
        ('/compensation', '0.8', 'weekly'),
        ('/program-reviews', '0.8', 'weekly'),
        ('/job-reviews', '0.8', 'weekly'),
        ('/knowledge-base', '0.7', 'monthly'),
        ('/wrvu-calculator', '0.7', 'monthly'),
        ('/calendar', '0.8', 'daily'),
    ]

    for path, priority, changefreq in static_pages:
        url_elem = ET.SubElement(urlset, 'url')
        ET.SubElement(url_elem, 'loc').text = url_for('home', _external=True).rstrip('/') + path
        ET.SubElement(url_elem, 'lastmod').text = datetime.now().strftime('%Y-%m-%d')
        ET.SubElement(url_elem, 'changefreq').text = changefreq
        ET.SubElement(url_elem, 'priority').text = priority

    # Dynamic pages - Opportunities
    try:
        opportunities = Opportunity.query.filter_by(is_active=True).limit(1000).all()
        for opp in opportunities:
            url_elem = ET.SubElement(urlset, 'url')
            ET.SubElement(url_elem, 'loc').text = url_for('opportunity_detail', id=opp.id, _external=True)
            ET.SubElement(url_elem, 'lastmod').text = opp.created_at.strftime('%Y-%m-%d')
            ET.SubElement(url_elem, 'changefreq').text = 'weekly'
            ET.SubElement(url_elem, 'priority').text = '0.7'
    except:
        pass  # Handle case where database might not be available

    # Dynamic pages - Forum Posts
    try:
        forum_posts = ForumPost.query.filter_by(is_locked=False).limit(500).all()
        for post in forum_posts:
            url_elem = ET.SubElement(urlset, 'url')
            ET.SubElement(url_elem, 'loc').text = url_for('view_post', post_id=post.id, _external=True)
            ET.SubElement(url_elem, 'lastmod').text = post.updated_at.strftime('%Y-%m-%d')
            ET.SubElement(url_elem, 'changefreq').text = 'monthly'
            ET.SubElement(url_elem, 'priority').text = '0.6'
    except:
        pass

    # Dynamic pages - Program Reviews
    try:
        program_reviews = ProgramReview.query.limit(200).all()
        for review in program_reviews:
            url_elem = ET.SubElement(urlset, 'url')
            ET.SubElement(url_elem, 'loc').text = url_for('program_reviews', _external=True) + f'#review-{review.id}'
            ET.SubElement(url_elem, 'lastmod').text = review.created_at.strftime('%Y-%m-%d')
            ET.SubElement(url_elem, 'changefreq').text = 'monthly'
            ET.SubElement(url_elem, 'priority').text = '0.5'
    except:
        pass

    # Convert to string
    xml_str = ET.tostring(urlset, encoding='unicode')
    
    return Response(xml_str, mimetype='application/xml')

@sitemap_bp.route('/robots.txt')
def robots():
    """Serve robots.txt file"""
    return Response(open('static/robots.txt').read(), mimetype='text/plain')
