from flask import Blueprint, render_template, redirect, url_for, request, abort
from flask_login import login_required, current_user
from .models import db, Conversation, Message, User, Opportunity, ResidentProfile

chat_bp = Blueprint("chat", __name__, url_prefix="/messages")


@chat_bp.route("/")
@login_required
def inbox():
	# Get conversations for the current user
	convos = Conversation.query.filter((Conversation.resident_id == current_user.id) | (Conversation.employer_id == current_user.id)).order_by(Conversation.created_at.desc()).all()
	
	# Add other user information for each conversation
	for convo in convos:
		if current_user.id == convo.resident_id:
			convo.other_user = convo.employer
		else:
			convo.other_user = convo.resident
		
		# Get the other user's profile photo
		if convo.other_user.role.value == 'resident':
			convo.other_user_profile = ResidentProfile.query.filter_by(user_id=convo.other_user.id).first()
		else:
			convo.other_user_profile = None
	
	return render_template("chat/inbox.html", convos=convos)


# Add a general message route to handle /message (singular) redirects
@chat_bp.route("/message")
@login_required
def message():
	return redirect(url_for("chat.inbox"))


@chat_bp.route("/start")
@login_required
def start():
	opportunity_id = request.args.get("opportunity_id", type=int)
	employer_id = request.args.get("employer_id", type=int)
	if not opportunity_id or not employer_id:
		abort(400)

	opp = Opportunity.query.get_or_404(opportunity_id)
	if current_user.role.value != "resident":
		abort(403)

	# Find existing conversation
	convo = Conversation.query.filter_by(opportunity_id=opp.id, resident_id=current_user.id, employer_id=employer_id).first()
	if not convo:
		convo = Conversation(opportunity_id=opp.id, resident_id=current_user.id, employer_id=employer_id)
		db.session.add(convo)
		db.session.commit()
	return redirect(url_for("chat.thread", conversation_id=convo.id))


@chat_bp.route("/direct")
@login_required
def direct():
	"""Start a direct conversation with another user"""
	# Get conversations for the current user
	convos = Conversation.query.filter((Conversation.resident_id == current_user.id) | (Conversation.employer_id == current_user.id)).order_by(Conversation.created_at.desc()).all()
	
	# Add other user information for each conversation
	for convo in convos:
		if current_user.id == convo.resident_id:
			convo.other_user = convo.employer
		else:
			convo.other_user = convo.resident
		
		# Get the other user's profile photo
		if convo.other_user.role.value == 'resident':
			convo.other_user_profile = ResidentProfile.query.filter_by(user_id=convo.other_user.id).first()
		else:
			convo.other_user_profile = None
	
	return render_template("chat/direct.html", convos=convos)


@chat_bp.route("/search-users")
@login_required
def search_users():
	"""Search for users to message"""
	query = request.args.get("q", "").strip()
	if not query:
		return {"users": []}
	
	# Search for users by name or email
	users = User.query.filter(
		(User.name.ilike(f"%{query}%") | User.email.ilike(f"%{query}%")) &
		(User.id != current_user.id)
	).limit(10).all()
	
	results = []
	for user in users:
		results.append({
			"id": user.id,
			"name": user.name,
			"email": user.email,
			"role": user.role.value,
			"organization": user.organization or ""
		})
	
	return {"users": results}


@chat_bp.route("/start-direct", methods=["POST"])
@login_required
def start_direct():
	"""Start a direct conversation with another user"""
	other_user_id = request.form.get("user_id", type=int)
	if not other_user_id:
		abort(400)
	
	other_user = User.query.get_or_404(other_user_id)
	if other_user.id == current_user.id:
		abort(400)
	
	# Check if conversation already exists
	convo = Conversation.query.filter(
		((Conversation.resident_id == current_user.id) & (Conversation.employer_id == other_user.id)) |
		((Conversation.resident_id == other_user.id) & (Conversation.employer_id == current_user.id))
	).filter(Conversation.opportunity_id.is_(None)).first()
	
	if not convo:
		# Create new direct conversation (no opportunity_id)
		if current_user.role.value == "resident":
			convo = Conversation(resident_id=current_user.id, employer_id=other_user.id)
		else:
			convo = Conversation(resident_id=other_user.id, employer_id=current_user.id)
		db.session.add(convo)
		db.session.commit()
	
	return redirect(url_for("chat.thread", conversation_id=convo.id))


@chat_bp.route("/<int:conversation_id>", methods=["GET", "POST"])
@login_required
def thread(conversation_id: int):
	convo = Conversation.query.get_or_404(conversation_id)
	if current_user.id not in (convo.resident_id, convo.employer_id):
		abort(403)

	if request.method == "POST":
		body = request.form.get("body", "").strip()
		if body:
			msg = Message(conversation_id=convo.id, sender_id=current_user.id, body=body)
			db.session.add(msg)
			
			# Update unread count for the other user
			other_id = convo.employer_id if current_user.id == convo.resident_id else convo.resident_id
			convo.unread_count += 1
			
			db.session.commit()
			return redirect(url_for("chat.thread", conversation_id=convo.id))

	# Mark messages as read when viewing the thread
	other_id = convo.employer_id if current_user.id == convo.resident_id else convo.resident_id
	unread_messages = Message.query.filter_by(conversation_id=convo.id, sender_id=other_id, is_read=False).all()
	for msg in unread_messages:
		msg.is_read = True
	
	# Reset unread count for current user
	convo.unread_count = 0
	db.session.commit()

	msgs = Message.query.filter_by(conversation_id=convo.id).order_by(Message.created_at.asc()).all()
	other_user = User.query.get(other_id)
	
	# Get the other user's profile photo for the template
	other_user_profile = None
	if other_user.role.value == 'resident':
		other_user_profile = ResidentProfile.query.filter_by(user_id=other_user.id).first()
	
	# Get the current user's profile photo for the template
	current_user_profile = None
	if current_user.role.value == 'resident':
		current_user_profile = ResidentProfile.query.filter_by(user_id=current_user.id).first()
	
	return render_template("chat/thread.html", convo=convo, msgs=msgs, other_user=other_user, other_user_profile=other_user_profile, current_user_profile=current_user_profile)


# Add a route outside the blueprint to handle /message (singular) URLs
def register_message_routes(app):
	@app.route("/message")
	@login_required
	def message_redirect():
		return redirect(url_for("chat.inbox"))


# Helper function to get unread message count for a user
def get_unread_count(user_id: int) -> int:
	return Conversation.query.filter(
		((Conversation.resident_id == user_id) | (Conversation.employer_id == user_id)) &
		(Conversation.unread_count > 0)
	).with_entities(db.func.sum(Conversation.unread_count)).scalar() or 0
