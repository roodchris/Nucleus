from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required, current_user
from sqlalchemy import and_, desc, asc, func, case, select
from sqlalchemy.orm import joinedload, selectinload
from .models import db, ForumPost, ForumComment, ForumVote, ForumCategory, User, ResidentProfile, EmployerProfile
from datetime import datetime
import os
import uuid
import json
from werkzeug.utils import secure_filename
from PIL import Image

forum_bp = Blueprint("forum", __name__)


@forum_bp.route("/forum")
def forum_index():
    """Main forum page showing all posts"""
    if not current_user.is_authenticated:
        return render_template("auth/login_required.html")
        
    page = request.args.get("page", 1, type=int)
    category = request.args.get("category", "")
    specialty = request.args.get("specialty", "")
    sort_by = request.args.get("sort", "newest")
    
    # Build query with dynamic specialty support
    from .enable_specialty_features import get_forum_query_with_specialty_support, should_enable_forum_specialty
    
    query = get_forum_query_with_specialty_support()
    
    # Filter by category if specified
    if category and category != "all":
        try:
            category_enum = ForumCategory(category)
            query = query.filter(ForumPost.category == category_enum)
        except ValueError:
            pass
    
    # Filter by specialty if specified and feature is enabled
    if specialty and should_enable_forum_specialty():
        try:
            query = query.filter(ForumPost.specialty == specialty)
        except Exception:
            # Ignore specialty filtering if there's an error
            pass
    
    # Sort posts
    if sort_by == "newest":
        query = query.order_by(ForumPost.created_at.desc())
    elif sort_by == "oldest":
        query = query.order_by(ForumPost.created_at.asc())
    elif sort_by == "most_voted":
        # Sort by net votes (upvotes - downvotes) descending
        # Use subqueries to calculate vote counts
        from sqlalchemy import select
        
        upvote_subquery = select(func.count(ForumVote.id)).where(
            and_(ForumVote.post_id == ForumPost.id, ForumVote.vote_type == "upvote")
        ).scalar_subquery()
        
        downvote_subquery = select(func.count(ForumVote.id)).where(
            and_(ForumVote.post_id == ForumPost.id, ForumVote.vote_type == "downvote")
        ).scalar_subquery()
        
        query = query.order_by((upvote_subquery - downvote_subquery).desc())
    elif sort_by == "most_commented":
        # Sort by comment count descending
        query = query.outerjoin(ForumComment, ForumPost.id == ForumComment.post_id).group_by(ForumPost.id).order_by(
            func.count(ForumComment.id).desc()
        )
    
    # Eager load author relationships to avoid N+1 queries
    query = query.options(joinedload(ForumPost.author))
    
    # Pagination
    posts = query.paginate(page=page, per_page=20, error_out=False)
    
    # Batch load comment counts for all posts in one query (exclude deleted comments from count)
    post_ids = [post.id for post in posts.items]
    if post_ids:
        comment_counts = db.session.query(
            ForumComment.post_id,
            func.count(ForumComment.id).label('count')
        ).filter(
            ForumComment.post_id.in_(post_ids),
            ForumComment.is_deleted == False
        ).group_by(ForumComment.post_id).all()
        comment_count_dict = {post_id: count for post_id, count in comment_counts}
    else:
        comment_count_dict = {}
    
    # Batch load vote counts for all posts in one query
    if post_ids:
        vote_counts = db.session.query(
            ForumVote.post_id,
            ForumVote.vote_type,
            func.count(ForumVote.id).label('count')
        ).filter(
            ForumVote.post_id.in_(post_ids),
            ForumVote.post_id.isnot(None)
        ).group_by(ForumVote.post_id, ForumVote.vote_type).all()
        
        # Build vote count dictionaries
        upvote_dict = {}
        downvote_dict = {}
        for post_id, vote_type, count in vote_counts:
            if vote_type == 'upvote':
                upvote_dict[post_id] = count
            elif vote_type == 'downvote':
                downvote_dict[post_id] = count
    else:
        upvote_dict = {}
        downvote_dict = {}
    
    # Batch load user vote states for all posts in one query
    user_vote_dict = {}
    if current_user and current_user.is_authenticated and post_ids:
        user_votes = ForumVote.query.filter(
            ForumVote.user_id == current_user.id,
            ForumVote.post_id.in_(post_ids),
            ForumVote.post_id.isnot(None)
        ).all()
        user_vote_dict = {vote.post_id: vote.vote_type for vote in user_votes}
    
    # Attach all data to posts
    for post in posts.items:
        post._comment_count = comment_count_dict.get(post.id, 0)
        upvotes = upvote_dict.get(post.id, 0)
        downvotes = downvote_dict.get(post.id, 0)
        post._total_votes = upvotes - downvotes
        post._user_vote = user_vote_dict.get(post.id, None)
    
    # Check if specialty features are enabled
    specialty_enabled = should_enable_forum_specialty()
    
    return render_template("forum/index.html", 
                         posts=posts, 
                         categories=ForumCategory,
                         current_category=category,
                         current_specialty=specialty if specialty_enabled else None,
                         specialty_enabled=specialty_enabled,
                         current_sort=sort_by)


@forum_bp.route("/forum/new", methods=["GET", "POST"])
@login_required
def new_post():
    """Create a new forum post"""
    from .enable_specialty_features import should_enable_forum_specialty
    
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        content = request.form.get("content", "").strip()
        category = request.form.get("category", "")
        specialty = request.form.get("specialty", "").strip() if should_enable_forum_specialty() else None
        photos_json = request.form.get("photos", "[]")
        
        if not title or not content or not category:
            flash("Please fill in all fields", "error")
            return render_template("forum/new_post.html", 
                               categories=ForumCategory,
                               specialty_enabled=should_enable_forum_specialty())
        
        try:
            category_enum = ForumCategory(category)
        except ValueError:
            flash("Invalid category selected", "error")
            return render_template("forum/new_post.html", 
                               categories=ForumCategory,
                               specialty_enabled=should_enable_forum_specialty())
        
        # Validate photos
        try:
            photos = json.loads(photos_json) if photos_json else []
            if len(photos) > MAX_PHOTOS_PER_POST:
                flash(f"Maximum {MAX_PHOTOS_PER_POST} photos allowed per post", "error")
                return render_template("forum/new_post.html", 
                                   categories=ForumCategory,
                                   specialty_enabled=should_enable_forum_specialty())
        except json.JSONDecodeError:
            photos = []
        
        # Create post with dynamic specialty support
        post_data = {
            'author_id': current_user.id,
            'title': title,
            'content': content,
            'category': category_enum,
            'photos': photos_json if photos else None
        }
        
        # Add specialty if the column exists and feature is enabled
        # Convert empty strings to None (for "General (All Specialties)" option)
        if should_enable_forum_specialty():
            # Check if the ForumPost model actually has the specialty attribute
            from .models import ForumPost
            if hasattr(ForumPost, 'specialty'):
                post_data['specialty'] = specialty if specialty else None
        
        try:
            post = ForumPost(**post_data)
        except TypeError as e:
            if 'specialty' in str(e):
                # Specialty column doesn't exist yet, create post without it
                post_data_without_specialty = {k: v for k, v in post_data.items() if k != 'specialty'}
                post = ForumPost(**post_data_without_specialty)
            else:
                raise e
        
        db.session.add(post)
        db.session.commit()
        
        flash("Post created successfully!", "success")
        return redirect(url_for("forum.view_post", post_id=post.id))
    
    return render_template("forum/new_post.html", 
                         categories=ForumCategory,
                         specialty_enabled=should_enable_forum_specialty())


@forum_bp.route("/forum/post/<int:post_id>")
def view_post(post_id):
    """View a specific forum post and its comments"""
    # Eager load author relationship
    post = ForumPost.query.options(joinedload(ForumPost.author)).get_or_404(post_id)
    sort_by = request.args.get("sort", "oldest")  # Changed default to oldest
    
    # Load ALL comments for this post in one query with eager loading (include deleted for tree structure)
    all_comments = ForumComment.query.filter_by(
        post_id=post_id
    ).options(
        joinedload(ForumComment.author)
    ).order_by(ForumComment.created_at.asc()).all()
    
    # Build comment tree structure in Python (much faster than recursive queries)
    comment_dict = {}  # id -> comment object
    top_level_comments = []
    
    # First pass: create dictionary and initialize replies list
    for comment in all_comments:
        comment.replies = []
        comment_dict[comment.id] = comment
    
    # Second pass: build tree structure (include deleted comments to maintain tree structure)
    for comment in all_comments:
        if comment.parent_comment_id is None:
            # Top-level comment (no parent)
            top_level_comments.append(comment)
        else:
            # This comment has a parent - try to attach it to the parent
            parent = comment_dict.get(comment.parent_comment_id)
            if parent:
                # Parent exists - attach as reply (even if parent is deleted)
                parent.replies.append(comment)
            else:
                # Parent not found - this shouldn't happen, but make it top-level as fallback
                top_level_comments.append(comment)
    
    # Helper function to sort replies recursively
    def sort_replies_recursive(comment):
        # Sort replies by created_at (oldest first for nested replies)
        comment.replies.sort(key=lambda c: c.created_at)
        # Recursively sort nested replies
        for reply in comment.replies:
            sort_replies_recursive(reply)
    
    # Sort replies within each comment
    for comment in top_level_comments:
        sort_replies_recursive(comment)
    
    # Sort top-level comments based on sort_by parameter
    if sort_by == "most_voted":
        # We'll sort by vote counts after loading them
        pass  # Will sort after loading vote data
    elif sort_by == "newest":
        top_level_comments.sort(key=lambda c: c.created_at, reverse=True)
    elif sort_by == "oldest":
        top_level_comments.sort(key=lambda c: c.created_at)
    # else: already sorted by created_at.asc() in query
    
    # Batch load vote counts for all comments in one query
    comment_ids = [c.id for c in all_comments]
    if comment_ids:
        vote_counts = db.session.query(
            ForumVote.comment_id,
            ForumVote.vote_type,
            func.count(ForumVote.id).label('count')
        ).filter(
            ForumVote.comment_id.in_(comment_ids),
            ForumVote.comment_id.isnot(None)
        ).group_by(ForumVote.comment_id, ForumVote.vote_type).all()
        
        # Build vote count dictionaries
        upvote_dict = {}
        downvote_dict = {}
        for comment_id, vote_type, count in vote_counts:
            if vote_type == 'upvote':
                upvote_dict[comment_id] = count
            elif vote_type == 'downvote':
                downvote_dict[comment_id] = count
    else:
        upvote_dict = {}
        downvote_dict = {}
    
    # Batch load user vote states for all comments in one query
    user_comment_vote_dict = {}
    if current_user and current_user.is_authenticated and comment_ids:
        user_votes = ForumVote.query.filter(
            ForumVote.user_id == current_user.id,
            ForumVote.comment_id.in_(comment_ids),
            ForumVote.comment_id.isnot(None)
        ).all()
        user_comment_vote_dict = {vote.comment_id: vote.vote_type for vote in user_votes}
    
    # Attach vote data to all comments (recursively)
    def attach_vote_data(comment):
        upvotes = upvote_dict.get(comment.id, 0)
        downvotes = downvote_dict.get(comment.id, 0)
        comment._total_votes = upvotes - downvotes
        comment._user_vote = user_comment_vote_dict.get(comment.id, None)
        
        # Process replies recursively
        for reply in comment.replies:
            attach_vote_data(reply)
    
    for comment in top_level_comments:
        attach_vote_data(comment)
    
    # Sort top-level comments by votes if needed
    if sort_by == "most_voted":
        top_level_comments.sort(key=lambda c: c._total_votes, reverse=True)
    
    # Add vote count and user vote state for the main post
    upvotes = ForumVote.query.filter_by(post_id=post.id, vote_type="upvote").count()
    downvotes = ForumVote.query.filter_by(post_id=post.id, vote_type="downvote").count()
    post._total_votes = upvotes - downvotes
    
    # Add user's current vote state if logged in
    if current_user.is_authenticated:
        user_vote = ForumVote.query.filter_by(
            user_id=current_user.id,
            post_id=post.id
        ).first()
        post._user_vote = user_vote.vote_type if user_vote else None
    else:
        post._user_vote = None
    
    # Calculate comment count excluding deleted comments
    non_deleted_count = sum(1 for c in all_comments if not c.is_deleted)
    
    return render_template("forum/view_post.html", 
                         post=post, 
                         comments=top_level_comments,
                         comment_count=non_deleted_count,
                         current_sort=sort_by)


@forum_bp.route("/forum/post/<int:post_id>/comment", methods=["POST"])
@login_required
def add_comment(post_id):
    """Add a comment to a forum post"""
    try:
        post = ForumPost.query.get_or_404(post_id)
        
        if post.is_locked:
            if request.headers.get('Content-Type') == 'application/x-www-form-urlencoded':
                return jsonify({"success": False, "error": "This post is locked and cannot be commented on"})
            flash("This post is locked and cannot be commented on", "error")
            return redirect(url_for("forum.view_post", post_id=post_id))
        
        content = request.form.get("content", "").strip()
        parent_comment_id = request.form.get("parent_comment_id", type=int)
        photos_json = request.form.get("photos", "[]")
        
        if not content:
            if request.headers.get('Content-Type') == 'application/x-www-form-urlencoded':
                return jsonify({"success": False, "error": "Comment cannot be empty"})
            flash("Comment cannot be empty", "error")
            return redirect(url_for("forum.view_post", post_id=post_id))
        
        # Validate photos
        try:
            photos = json.loads(photos_json) if photos_json else []
            if len(photos) > MAX_PHOTOS_PER_COMMENT:
                if request.headers.get('Content-Type') == 'application/x-www-form-urlencoded':
                    return jsonify({"success": False, "error": f"Maximum {MAX_PHOTOS_PER_COMMENT} photos allowed per comment"})
                flash(f"Maximum {MAX_PHOTOS_PER_COMMENT} photos allowed per comment", "error")
                return redirect(url_for("forum.view_post", post_id=post_id))
        except json.JSONDecodeError:
            photos = []
        
        comment = ForumComment(
            post_id=post_id,
            author_id=current_user.id,
            parent_comment_id=parent_comment_id,
            content=content,
            photos=photos_json if photos else None
        )
        
        db.session.add(comment)
        db.session.commit()
        
        # Check if this is an AJAX request - use query parameter for reliability
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                "success": True,
                "comment": {
                    "id": comment.id,
                    "content": comment.content,
                    "author_name": comment.author.name,
                    "created_at": comment.created_at.isoformat(),
                    "is_deleted": comment.is_deleted,
                    "photos": photos
                }
            })
        
        flash("Comment added successfully!", "success")
        return redirect(url_for("forum.view_post", post_id=post_id))
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error posting comment: {str(e)}", exc_info=True)
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({"success": False, "error": f"Error posting comment: {str(e)}"})
        
        flash(f"Error posting comment: {str(e)}", "error")
        return redirect(url_for("forum.view_post", post_id=post_id))


@forum_bp.route("/forum/comment/<int:comment_id>/reply", methods=["POST"])
@login_required
def reply_to_comment(comment_id):
    """Reply to a specific comment"""
    try:
        parent_comment = ForumComment.query.get_or_404(comment_id)
        post = parent_comment.post
        
        if post.is_locked:
            if request.headers.get('Content-Type') == 'application/x-www-form-urlencoded':
                return jsonify({"success": False, "error": "This post is locked and cannot be commented on"})
            flash("This post is locked and cannot be commented on", "error")
            return redirect(url_for("forum.view_post", post_id=post.id))
        
        content = request.form.get("content", "").strip()
        
        if not content:
            if request.headers.get('Content-Type') == 'application/x-www-form-urlencoded':
                return jsonify({"success": False, "error": "Reply cannot be empty"})
            flash("Reply cannot be empty", "error")
            return redirect(url_for("forum.view_post", post_id=post.id))
        
        reply = ForumComment(
            post_id=post.id,
            author_id=current_user.id,
            parent_comment_id=comment_id,
            content=content
        )
        
        db.session.add(reply)
        db.session.commit()
        
        # Check if this is an AJAX request - use query parameter for reliability
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                "success": True,
                "reply": {
                    "id": reply.id,
                    "content": reply.content,
                    "author_name": reply.author.name,
                    "created_at": reply.created_at.isoformat(),
                    "is_deleted": reply.is_deleted
                }
            })
        
        flash("Reply posted successfully!", "success")
        return redirect(url_for("forum.view_post", post_id=post.id))
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error posting reply: {str(e)}", exc_info=True)
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({"success": False, "error": f"Error posting reply: {str(e)}"})
        
        flash(f"Error posting reply: {str(e)}", "error")
        return redirect(url_for("forum.view_post", post_id=post.id if 'post' in locals() else comment_id))


@forum_bp.route("/forum/vote", methods=["POST"])
@login_required
def vote():
    """Handle upvoting and downvoting"""
    data = request.get_json()
    post_id = data.get("post_id")
    comment_id = data.get("comment_id")
    vote_type = data.get("vote_type")  # "upvote" or "downvote"
    
    if vote_type not in ["upvote", "downvote"]:
        return jsonify({"error": "Invalid vote type"}), 400
    
    # Convert string IDs to integers if they exist
    if post_id is not None:
        try:
            post_id = int(post_id)
        except (ValueError, TypeError):
            return jsonify({"error": "Invalid post ID"}), 400
    
    if comment_id is not None:
        try:
            comment_id = int(comment_id)
        except (ValueError, TypeError):
            return jsonify({"error": "Invalid comment ID"}), 400
    
    # Check if user already voted
    existing_vote = ForumVote.query.filter_by(
        user_id=current_user.id,
        post_id=post_id,
        comment_id=comment_id
    ).first()
    
    if existing_vote:
        if existing_vote.vote_type == vote_type:
            # Remove vote if clicking same button
            db.session.delete(existing_vote)
            db.session.commit()
            
            # Calculate new totals
            if post_id:
                upvotes = ForumVote.query.filter_by(post_id=post_id, vote_type="upvote").count()
                downvotes = ForumVote.query.filter_by(post_id=post_id, vote_type="downvote").count()
                total_votes = upvotes - downvotes
            else:
                upvotes = ForumVote.query.filter_by(comment_id=comment_id, vote_type="upvote").count()
                downvotes = ForumVote.query.filter_by(comment_id=comment_id, vote_type="downvote").count()
                total_votes = upvotes - downvotes
            
            return jsonify({
                "success": True,
                "action": "removed",
                "total_votes": total_votes,
                "user_vote": None
            })
        else:
            # Change vote type
            existing_vote.vote_type = vote_type
            db.session.commit()
            
            # Calculate new totals
            if post_id:
                upvotes = ForumVote.query.filter_by(post_id=post_id, vote_type="upvote").count()
                downvotes = ForumVote.query.filter_by(post_id=post_id, vote_type="downvote").count()
                total_votes = upvotes - downvotes
            else:
                upvotes = ForumVote.query.filter_by(comment_id=comment_id, vote_type="upvote").count()
                downvotes = ForumVote.query.filter_by(comment_id=comment_id, vote_type="downvote").count()
                total_votes = upvotes - downvotes
            
            return jsonify({
                "success": True,
                "action": "changed",
                "total_votes": total_votes,
                "user_vote": vote_type
            })
    else:
        # Create new vote
        vote = ForumVote(
            user_id=current_user.id,
            post_id=post_id,
            comment_id=comment_id,
            vote_type=vote_type
        )
        db.session.add(vote)
        db.session.commit()
        
        # Calculate new totals
        if post_id:
            upvotes = ForumVote.query.filter_by(post_id=post_id, vote_type="upvote").count()
            downvotes = ForumVote.query.filter_by(post_id=post_id, vote_type="downvote").count()
            total_votes = upvotes - downvotes
        else:
            upvotes = ForumVote.query.filter_by(comment_id=comment_id, vote_type="upvote").count()
            downvotes = ForumVote.query.filter_by(comment_id=comment_id, vote_type="downvote").count()
            total_votes = upvotes - downvotes
        
        return jsonify({
            "success": True,
            "action": "added",
            "total_votes": total_votes,
            "user_vote": vote_type
        })




@forum_bp.route("/forum/comment/<int:comment_id>/edit", methods=["POST"])
@login_required
def edit_comment(comment_id):
    """Edit a comment"""
    comment = ForumComment.query.get_or_404(comment_id)
    
    if comment.author_id != current_user.id:
        if (request.headers.get('Content-Type') == 'application/x-www-form-urlencoded' or 
            request.headers.get('X-Requested-With') == 'XMLHttpRequest'):
            return jsonify({"success": False, "error": "You can only edit your own comments"})
        flash("You can only edit your own comments", "error")
        return redirect(url_for("forum.view_post", post_id=comment.post_id))
    
    content = request.form.get("content", "").strip()
    
    if not content:
        if (request.headers.get('Content-Type') == 'application/x-www-form-urlencoded' or 
            request.headers.get('X-Requested-With') == 'XMLHttpRequest'):
            return jsonify({"success": False, "error": "Comment cannot be empty"})
        flash("Comment cannot be empty", "error")
        return redirect(url_for("forum.view_post", post_id=comment.post_id))
    
    comment.content = content
    comment.is_edited = True
    comment.updated_at = datetime.utcnow()
    
    db.session.commit()
    
    # Check if this is an AJAX request - use query parameter for reliability
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({
            "success": True,
            "comment": {
                "id": comment.id,
                "content": comment.content,
                "is_edited": comment.is_edited
            }
        })
    
    flash("Comment updated successfully!", "success")
    return redirect(url_for("forum.view_post", post_id=comment.post_id))


@forum_bp.route("/forum/comment/<int:comment_id>/delete", methods=["POST"])
@login_required
def delete_comment(comment_id):
    """Delete a comment"""
    comment = ForumComment.query.get_or_404(comment_id)
    
    if comment.author_id != current_user.id:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({"success": False, "error": "You can only delete your own comments"})
        flash("You can only delete your own comments", "error")
        return redirect(url_for("forum.view_post", post_id=comment.post_id))
    
    # Soft delete - mark as deleted instead of actually deleting
    comment.is_deleted = True
    comment.updated_at = datetime.utcnow()
    
    db.session.commit()
    
    # Check if this is an AJAX request
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({"success": True})
    
    flash("Comment deleted successfully!", "success")
    return redirect(url_for("forum.view_post", post_id=comment.post_id))


@forum_bp.route("/forum/post/<int:post_id>/delete", methods=["POST"])
@login_required
def delete_post(post_id):
    """Delete a forum post"""
    post = ForumPost.query.get_or_404(post_id)
    
    if post.author_id != current_user.id:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({"success": False, "error": "You can only delete your own posts"})
        flash("You can only delete your own posts", "error")
        return redirect(url_for("forum.view_post", post_id=post_id))
    
    # Delete all votes associated with this post first
    ForumVote.query.filter_by(post_id=post_id).delete()
    
    # Delete all comments and their votes
    for comment in post.comments:
        ForumVote.query.filter_by(comment_id=comment.id).delete()
        db.session.delete(comment)
    
    # Finally delete the post
    db.session.delete(post)
    db.session.commit()
    
    # Check if this is an AJAX request
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({"success": True})
    
    flash("Post deleted successfully!", "success")
    return redirect(url_for("forum.forum_index"))


@forum_bp.route("/forum/post/<int:post_id>/edit", methods=["GET", "POST"])
@login_required
def edit_post(post_id):
    """Edit a forum post"""
    post = ForumPost.query.get_or_404(post_id)
    
    if post.author_id != current_user.id:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({"success": False, "error": "You can only edit your own posts"})
        flash("You can only edit your own posts", "error")
        return redirect(url_for("forum.view_post", post_id=post_id))
    
    if request.method == "POST":
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()
        
        if not title or not content:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({"success": False, "error": "Title and content cannot be empty"})
            flash("Title and content cannot be empty", "error")
            return render_template("forum/edit_post.html", post=post, categories=ForumCategory)
        
        post.title = title
        post.content = content
        post.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({"success": True})
        
        flash("Post updated successfully!", "success")
        return redirect(url_for("forum.view_post", post_id=post_id))
    
    return render_template("forum/edit_post.html", post=post, categories=ForumCategory)




@forum_bp.route("/forum/post/<int:post_id>/comments")
def get_comments(post_id):
    """Get just the comments section for a post (for AJAX reload)"""
    try:
        post = ForumPost.query.get_or_404(post_id)
        sort_by = request.args.get("sort", "oldest")
        current_app.logger.info(f"Getting comments for post {post_id}, sort: {sort_by}")
        
        # Load ALL comments for this post in one query with eager loading (include deleted for tree structure)
        all_comments = ForumComment.query.filter_by(
            post_id=post_id
        ).options(
            joinedload(ForumComment.author)
        ).order_by(ForumComment.created_at.asc()).all()
        
        # Build comment tree structure in Python
        comment_dict = {}  # id -> comment object
        top_level_comments = []
        
        # First pass: create dictionary and initialize replies list
        for comment in all_comments:
            comment.replies = []
            comment_dict[comment.id] = comment
        
        # Second pass: build tree structure (include deleted comments to maintain tree structure)
        for comment in all_comments:
            if comment.parent_comment_id is None:
                # Top-level comment (no parent)
                top_level_comments.append(comment)
            else:
                # This comment has a parent - try to attach it to the parent
                parent = comment_dict.get(comment.parent_comment_id)
                if parent:
                    # Parent exists - attach as reply (even if parent is deleted)
                    parent.replies.append(comment)
                else:
                    # Parent not found - this shouldn't happen, but make it top-level as fallback
                    top_level_comments.append(comment)
        
        # Helper function to sort replies recursively
        def sort_replies_recursive(comment):
            # Sort replies by created_at (oldest first for nested replies)
            comment.replies.sort(key=lambda c: c.created_at)
            # Recursively sort nested replies
            for reply in comment.replies:
                sort_replies_recursive(reply)
        
        # Sort replies within each comment
        for comment in top_level_comments:
            sort_replies_recursive(comment)
        
        # Sort top-level comments based on sort_by parameter
        if sort_by == "most_voted":
            pass  # Will sort after loading vote data
        elif sort_by == "newest" or sort_by == "most_recent":
            top_level_comments.sort(key=lambda c: c.created_at, reverse=True)
        elif sort_by == "oldest":
            top_level_comments.sort(key=lambda c: c.created_at)
        # else: already sorted by created_at.asc() in query
        
        # Batch load vote counts for all comments in one query
        comment_ids = [c.id for c in all_comments]
        if comment_ids:
            vote_counts = db.session.query(
                ForumVote.comment_id,
                ForumVote.vote_type,
                func.count(ForumVote.id).label('count')
            ).filter(
                ForumVote.comment_id.in_(comment_ids),
                ForumVote.comment_id.isnot(None)
            ).group_by(ForumVote.comment_id, ForumVote.vote_type).all()
            
            # Build vote count dictionaries
            upvote_dict = {}
            downvote_dict = {}
            for comment_id, vote_type, count in vote_counts:
                if vote_type == 'upvote':
                    upvote_dict[comment_id] = count
                elif vote_type == 'downvote':
                    downvote_dict[comment_id] = count
        else:
            upvote_dict = {}
            downvote_dict = {}
        
        # Batch load user vote states for all comments in one query
        user_comment_vote_dict = {}
        if current_user and current_user.is_authenticated and comment_ids:
            user_votes = ForumVote.query.filter(
                ForumVote.user_id == current_user.id,
                ForumVote.comment_id.in_(comment_ids),
                ForumVote.comment_id.isnot(None)
            ).all()
            user_comment_vote_dict = {vote.comment_id: vote.vote_type for vote in user_votes}
        
        # Attach vote data to all comments (recursively)
        def attach_vote_data(comment):
            upvotes = upvote_dict.get(comment.id, 0)
            downvotes = downvote_dict.get(comment.id, 0)
            comment._total_votes = upvotes - downvotes
            comment._user_vote = user_comment_vote_dict.get(comment.id, None)
            
            # Process replies recursively
            for reply in comment.replies:
                attach_vote_data(reply)
        
        for comment in top_level_comments:
            attach_vote_data(comment)
        
        # Sort top-level comments by votes if needed
        if sort_by == "most_voted":
            top_level_comments.sort(key=lambda c: c._total_votes, reverse=True)
        elif sort_by == "most_downvoted":
            top_level_comments.sort(key=lambda c: c._total_votes)  # Ascending (most negative first)
        
        # Calculate comment count excluding deleted comments
        non_deleted_count = sum(1 for c in all_comments if not c.is_deleted)
        
        # Render just the comments section
        return render_template("forum/comments_section.html", 
                             post=post, 
                             comments=top_level_comments,
                             comment_count=non_deleted_count,
                             current_sort=sort_by)
    
    except Exception as e:
        current_app.logger.error(f"Error getting comments for post {post_id}: {str(e)}", exc_info=True)
        return f"Error loading comments: {str(e)}", 500


# Photo upload functionality
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
MAX_PHOTOS_PER_POST = 5
MAX_PHOTOS_PER_COMMENT = 3

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def resize_image(image_path, max_width=1200, max_height=1200, quality=85):
    """Resize image to fit within max dimensions while maintaining aspect ratio"""
    try:
        with Image.open(image_path) as img:
            # Convert to RGB if necessary
            if img.mode in ('RGBA', 'LA', 'P'):
                img = img.convert('RGB')
            
            # Calculate new dimensions
            width, height = img.size
            if width <= max_width and height <= max_height:
                return  # No resize needed
            
            # Calculate new size maintaining aspect ratio
            ratio = min(max_width/width, max_height/height)
            new_width = int(width * ratio)
            new_height = int(height * ratio)
            
            # Resize image
            img_resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            img_resized.save(image_path, 'JPEG', quality=quality, optimize=True)
    except Exception as e:
        print(f"Error resizing image {image_path}: {e}")

@forum_bp.route("/api/upload-photo", methods=["POST"])
@login_required
def upload_photo():
    """Upload a photo for forum posts or comments"""
    try:
        if 'photo' not in request.files:
            return jsonify({'success': False, 'error': 'No photo provided'}), 400
        
        file = request.files['photo']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No photo selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'success': False, 'error': 'Invalid file type. Allowed: PNG, JPG, JPEG, GIF, WEBP'}), 400
        
        # Check file size
        file.seek(0, 2)  # Seek to end
        file_size = file.tell()
        file.seek(0)  # Reset to beginning
        
        if file_size > MAX_FILE_SIZE:
            return jsonify({'success': False, 'error': 'File too large. Maximum size: 5MB'}), 400
        
        # Generate unique filename
        filename = secure_filename(file.filename)
        name, ext = os.path.splitext(filename)
        unique_filename = f"{uuid.uuid4().hex}{ext}"
        
        # Save file
        upload_dir = os.path.join(current_app.static_folder, 'uploads', 'photos')
        os.makedirs(upload_dir, exist_ok=True)
        file_path = os.path.join(upload_dir, unique_filename)
        file.save(file_path)
        
        # Resize image
        resize_image(file_path)
        
        return jsonify({
            'success': True, 
            'filename': unique_filename,
            'url': f'/static/uploads/photos/{unique_filename}'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@forum_bp.route("/api/delete-photo", methods=["POST"])
@login_required
def delete_photo():
    """Delete a photo from the server"""
    try:
        data = request.get_json()
        filename = data.get('filename')
        
        if not filename:
            return jsonify({'success': False, 'error': 'No filename provided'}), 400
        
        # Security check - ensure filename is safe
        filename = secure_filename(filename)
        file_path = os.path.join(current_app.static_folder, 'uploads', 'photos', filename)
        
        if os.path.exists(file_path):
            os.remove(file_path)
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'File not found'}), 404
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
