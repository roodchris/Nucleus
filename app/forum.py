from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from sqlalchemy import and_, desc, asc, func, case
from .models import db, ForumPost, ForumComment, ForumVote, ForumCategory, User, ResidentProfile, EmployerProfile
from datetime import datetime

forum_bp = Blueprint("forum", __name__)


@forum_bp.route("/forum")
def forum_index():
    """Main forum page showing all posts"""
    if not current_user.is_authenticated:
        return render_template("auth/login_required.html")
        
    page = request.args.get("page", 1, type=int)
    category = request.args.get("category", "")
    sort_by = request.args.get("sort", "newest")
    
    # Build query
    query = ForumPost.query
    
    # Filter by category if specified
    if category and category != "all":
        try:
            category_enum = ForumCategory(category)
            query = query.filter(ForumPost.category == category_enum)
        except ValueError:
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
    
    # Pagination
    posts = query.paginate(page=page, per_page=20, error_out=False)
    
    # Get comment counts and vote counts for each post
    for post in posts.items:
        # Add comment count and vote count as attributes (not properties)
        post._comment_count = ForumComment.query.filter_by(post_id=post.id).count()
        
        # Add vote count
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
    
    return render_template("forum/index.html", 
                         posts=posts, 
                         categories=ForumCategory,
                         current_category=category,
                         current_sort=sort_by)


@forum_bp.route("/forum/new", methods=["GET", "POST"])
@login_required
def new_post():
    """Create a new forum post"""
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        content = request.form.get("content", "").strip()
        category = request.form.get("category", "")
        
        if not title or not content or not category:
            flash("Please fill in all fields", "error")
            return render_template("forum/new_post.html", categories=ForumCategory)
        
        try:
            category_enum = ForumCategory(category)
        except ValueError:
            flash("Invalid category selected", "error")
            return render_template("forum/new_post.html", categories=ForumCategory)
        
        post = ForumPost(
            author_id=current_user.id,
            title=title,
            content=content,
            category=category_enum
        )
        
        db.session.add(post)
        db.session.commit()
        
        flash("Post created successfully!", "success")
        return redirect(url_for("forum.view_post", post_id=post.id))
    
    return render_template("forum/new_post.html", categories=ForumCategory)


@forum_bp.route("/forum/post/<int:post_id>")
def view_post(post_id):
    """View a specific forum post and its comments"""
    post = ForumPost.query.get_or_404(post_id)
    sort_by = request.args.get("sort", "most_voted")
    
    # Get top-level comments (no parent) with proper sorting
    if sort_by == "most_voted":
        # For now, just show most recent since we can't use properties in queries
        comments = ForumComment.query.filter_by(post_id=post_id, parent_comment_id=None).order_by(ForumComment.created_at.desc()).all()
    elif sort_by == "most_downvoted":
        # For now, just show most recent since we can't use properties in queries
        comments = ForumComment.query.filter_by(post_id=post_id, parent_comment_id=None).order_by(ForumComment.created_at.desc()).all()
    elif sort_by == "most_recent":
        comments = ForumComment.query.filter_by(post_id=post_id, parent_comment_id=None).order_by(ForumComment.created_at.desc()).all()
    elif sort_by == "oldest":
        comments = ForumComment.query.filter_by(post_id=post_id, parent_comment_id=None).order_by(ForumComment.created_at.asc()).all()
    else:
        comments = ForumComment.query.filter_by(post_id=post_id, parent_comment_id=None).order_by(ForumComment.created_at.desc()).all()
    
    # Get all replies for each comment (recursively)
    def get_replies_with_nesting(comment):
        replies = ForumComment.query.filter_by(parent_comment_id=comment.id).order_by(ForumComment.created_at.asc()).all()
        for reply in replies:
            reply.replies = get_replies_with_nesting(reply)
        return replies
    
    for comment in comments:
        comment.replies = get_replies_with_nesting(comment)
    
    # Add vote counts and user vote states to comments and replies (recursively)
    def add_vote_data(comment):
        upvotes = ForumVote.query.filter_by(comment_id=comment.id, vote_type="upvote").count()
        downvotes = ForumVote.query.filter_by(comment_id=comment.id, vote_type="downvote").count()
        comment._total_votes = upvotes - downvotes
        
        # Add user's current vote state if logged in
        if current_user.is_authenticated:
            user_vote = ForumVote.query.filter_by(
                user_id=current_user.id,
                comment_id=comment.id
            ).first()
            comment._user_vote = user_vote.vote_type if user_vote else None
        else:
            comment._user_vote = None
        
        # Process replies recursively
        for reply in comment.replies:
            add_vote_data(reply)
    
    for comment in comments:
        add_vote_data(comment)
    
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
    
    return render_template("forum/view_post.html", 
                         post=post, 
                         comments=comments,
                         current_sort=sort_by)


@forum_bp.route("/forum/post/<int:post_id>/comment", methods=["POST"])
@login_required
def add_comment(post_id):
    """Add a comment to a forum post"""
    post = ForumPost.query.get_or_404(post_id)
    
    if post.is_locked:
        if request.headers.get('Content-Type') == 'application/x-www-form-urlencoded':
            return jsonify({"success": False, "error": "This post is locked and cannot be commented on"})
        flash("This post is locked and cannot be commented on", "error")
        return redirect(url_for("forum.view_post", post_id=post_id))
    
    content = request.form.get("content", "").strip()
    parent_comment_id = request.form.get("parent_comment_id", type=int)
    
    if not content:
        if request.headers.get('Content-Type') == 'application/x-www-form-urlencoded':
            return jsonify({"success": False, "error": "Comment cannot be empty"})
        flash("Comment cannot be empty", "error")
        return redirect(url_for("forum.view_post", post_id=post_id))
    
    comment = ForumComment(
        post_id=post_id,
        author_id=current_user.id,
        parent_comment_id=parent_comment_id,
        content=content
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
                "is_deleted": comment.is_deleted
            }
        })
    
    flash("Comment added successfully!", "success")
    return redirect(url_for("forum.view_post", post_id=post_id))


@forum_bp.route("/forum/comment/<int:comment_id>/reply", methods=["POST"])
@login_required
def reply_to_comment(comment_id):
    """Reply to a specific comment"""
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
    post = ForumPost.query.get_or_404(post_id)
    sort_by = request.args.get("sort", "most_voted")
    
    # Get top-level comments (no parent) with proper sorting
    if sort_by == "most_voted":
        # For now, just show most recent since we can't use properties in queries
        comments = ForumComment.query.filter_by(post_id=post_id, parent_comment_id=None).order_by(ForumComment.created_at.desc()).all()
    elif sort_by == "most_downvoted":
        # For now, just show most recent since we can't use properties in queries
        comments = ForumComment.query.filter_by(post_id=post_id, parent_comment_id=None).order_by(ForumComment.created_at.desc()).all()
    elif sort_by == "most_recent":
        comments = ForumComment.query.filter_by(post_id=post_id, parent_comment_id=None).order_by(ForumComment.created_at.desc()).all()
    elif sort_by == "oldest":
        comments = ForumComment.query.filter_by(post_id=post_id, parent_comment_id=None).order_by(ForumComment.created_at.asc()).all()
    else:
        comments = ForumComment.query.filter_by(post_id=post_id, parent_comment_id=None).order_by(ForumComment.created_at.desc()).all()
    
    # Get all replies for each comment (recursively)
    def get_replies_with_nesting(comment):
        replies = ForumComment.query.filter_by(parent_comment_id=comment.id).order_by(ForumComment.created_at.asc()).all()
        for reply in replies:
            reply.replies = get_replies_with_nesting(reply)
        return replies
    
    for comment in comments:
        comment.replies = get_replies_with_nesting(comment)
    
    # Add vote counts and user vote states to comments and replies (recursively)
    def add_vote_data(comment):
        upvotes = ForumVote.query.filter_by(comment_id=comment.id, vote_type="upvote").count()
        downvotes = ForumVote.query.filter_by(comment_id=comment.id, vote_type="downvote").count()
        comment._total_votes = upvotes - downvotes
        
        # Add user's current vote state if logged in
        if current_user.is_authenticated:
            user_vote = ForumVote.query.filter_by(
                user_id=current_user.id,
                comment_id=comment.id
            ).first()
            comment._user_vote = user_vote.vote_type if user_vote else None
        else:
            comment._user_vote = None
        
        # Process replies recursively
        for reply in comment.replies:
            add_vote_data(reply)
    
    for comment in comments:
        add_vote_data(comment)
    
    # Render just the comments section
    return render_template("forum/comments_section.html", 
                         post=post, 
                         comments=comments,
                         current_sort=sort_by)
