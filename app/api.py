from flask import Blueprint, jsonify, request, current_app
from flask_login import login_required, current_user
from app.models import Conversation, Message, User, ResidentProfile, EmployerProfile
from app import db
from sqlalchemy import desc, and_
from datetime import datetime
import uuid
from app.models import UserSession

api_bp = Blueprint('api', __name__, url_prefix='/api')

@api_bp.route('/conversations/recent')
@login_required
def recent_conversations():
    """Get recent conversations for the current user, consolidated by user"""
    try:
        # Get all conversations where current user is involved
        all_conversations = Conversation.query.filter(
            (Conversation.resident_id == current_user.id) | 
            (Conversation.employer_id == current_user.id)
        ).all()
        
        # Group conversations by the other user
        user_conversations = {}
        total_unread = 0
        
        for conv in all_conversations:
            # Determine the other user
            if conv.resident_id == current_user.id:
                other_user_id = conv.employer_id
                other_user = conv.employer
                unread_count = conv.unread_count
            else:
                other_user_id = conv.resident_id
                other_user = conv.resident
                unread_count = conv.unread_count
            
            # If we haven't seen this user before, initialize their data
            if other_user_id not in user_conversations:
                # Get the other user's profile
                other_profile = None
                if other_user.role.value == 'resident':
                    other_profile = ResidentProfile.query.filter_by(user_id=other_user.id).first()
                elif other_user.role.value == 'employer':
                    other_profile = EmployerProfile.query.filter_by(user_id=other_user.id).first()
                
                user_conversations[other_user_id] = {
                    'other_user': {
                        'id': other_user.id,
                        'name': other_user.name,
                        'role': other_user.role.value,
                        'is_online': other_user.is_online()
                    },
                    'other_user_profile': {
                        'photo_filename': other_profile.photo_filename if other_profile else None
                    } if other_profile else None,
                    'conversation_ids': [],
                    'total_unread': 0,
                    'last_message': None,
                    'last_activity': None
                }
            
            # Add this conversation to the user's list
            user_conversations[other_user_id]['conversation_ids'].append(conv.id)
            user_conversations[other_user_id]['total_unread'] += unread_count
            
            # Get the last message from this conversation
            last_message = Message.query.filter_by(conversation_id=conv.id).order_by(desc(Message.created_at)).first()
            
            # Update the user's last message and activity if this conversation is more recent
            if last_message:
                if (user_conversations[other_user_id]['last_activity'] is None or 
                    last_message.created_at > user_conversations[other_user_id]['last_activity']):
                    user_conversations[other_user_id]['last_message'] = last_message.body
                    user_conversations[other_user_id]['last_activity'] = last_message.created_at
            
            # Also check conversation creation time
            if (user_conversations[other_user_id]['last_activity'] is None or 
                conv.created_at > user_conversations[other_user_id]['last_activity']):
                user_conversations[other_user_id]['last_activity'] = conv.created_at
        
        # Convert to list and sort by last activity
        conversation_data = []
        for user_id, user_data in user_conversations.items():
            # Use the first conversation ID as the primary ID for the consolidated thread
            primary_conversation_id = user_data['conversation_ids'][0]
            
            conversation_data.append({
                'id': primary_conversation_id,
                'conversation_ids': user_data['conversation_ids'],  # All related conversation IDs
                'other_user': user_data['other_user'],
                'other_user_profile': user_data['other_user_profile'],
                'last_message': user_data['last_message'],
                'updated_at': user_data['last_activity'].isoformat() if user_data['last_activity'] else None,
                'unread_count': user_data['total_unread']
            })
            
            total_unread += user_data['total_unread']
        
        # Sort by last activity (most recent first) and limit to 10
        conversation_data.sort(key=lambda x: x['updated_at'] or '', reverse=True)
        conversation_data = conversation_data[:10]
        
        return jsonify({
            'conversations': conversation_data,
            'unread_count': total_unread
        })
        
    except Exception as e:
        current_app.logger.error(f"Error fetching recent conversations: {str(e)}")
        return jsonify({'error': 'Failed to fetch conversations'}), 500

@api_bp.route('/conversations/<int:conversation_id>/messages')
@login_required
def conversation_messages(conversation_id):
    """Get messages for a specific conversation, including all related conversations"""
    try:
        # Verify user has access to this conversation
        conversation = Conversation.query.filter(
            and_(
                (Conversation.resident_id == current_user.id) | (Conversation.employer_id == current_user.id),
                Conversation.id == conversation_id
            )
        ).first()
        
        if not conversation:
            return jsonify({'error': 'Conversation not found'}), 404
        
        # Determine the other user
        if conversation.resident_id == current_user.id:
            other_user = conversation.employer
            other_user_id = conversation.employer_id
        else:
            other_user = conversation.resident
            other_user_id = conversation.resident_id
        
        # Find all conversations with this user
        related_conversations = Conversation.query.filter(
            and_(
                ((Conversation.resident_id == current_user.id) & (Conversation.employer_id == other_user_id)) |
                ((Conversation.resident_id == other_user_id) & (Conversation.employer_id == current_user.id))
            )
        ).all()
        
        # Get messages from all related conversations
        all_messages = []
        for conv in related_conversations:
            messages = Message.query.filter_by(conversation_id=conv.id).order_by(Message.created_at).all()
            for msg in messages:
                all_messages.append({
                    'id': msg.id,
                    'content': msg.body,
                    'user_id': msg.sender_id,
                    'timestamp': msg.created_at.isoformat() if msg.created_at else None,
                    'conversation_id': conv.id
                })
        
        # Sort all messages by timestamp
        all_messages.sort(key=lambda x: x['timestamp'] or '')
        
        # Mark all messages as read in all related conversations
        for conv in related_conversations:
            conv.unread_count = 0
        
        db.session.commit()
        
        return jsonify({
            'messages': all_messages,
            'other_user': {
                'id': other_user.id,
                'name': other_user.name,
                'role': other_user.role.value
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Error fetching conversation messages: {str(e)}")
        return jsonify({'error': 'Failed to fetch messages'}), 500

@api_bp.route('/messages/send', methods=['POST'])
@login_required
def send_message():
    """Send a new message to any conversation with the same user"""
    try:
        data = request.get_json()
        conversation_id = data.get('conversation_id')
        content = data.get('content')
        
        if not conversation_id or not content:
            return jsonify({'error': 'Missing conversation_id or content'}), 400
        
        # Verify user has access to this conversation
        conversation = Conversation.query.filter(
            and_(
                (Conversation.resident_id == current_user.id) | (Conversation.employer_id == current_user.id),
                Conversation.id == conversation_id
            )
        ).first()
        
        if not conversation:
            return jsonify({'error': 'Conversation not found'}), 404
        
        # Determine the other user
        if conversation.resident_id == current_user.id:
            other_user_id = conversation.employer_id
        else:
            other_user_id = conversation.resident_id
        
        # Find the most recent conversation with this user to add the message to
        # This ensures messages go to the most recent conversation thread
        most_recent_conversation = Conversation.query.filter(
            and_(
                ((Conversation.resident_id == current_user.id) & (Conversation.employer_id == other_user_id)) |
                ((Conversation.resident_id == other_user_id) & (Conversation.employer_id == current_user.id))
            )
        ).order_by(desc(Conversation.created_at)).first()
        
        if not most_recent_conversation:
            return jsonify({'error': 'No conversation found with this user'}), 404
        
        # Create new message in the most recent conversation
        message = Message(
            conversation_id=most_recent_conversation.id,
            sender_id=current_user.id,
            body=content,
            created_at=datetime.utcnow()
        )
        
        db.session.add(message)
        
        # Update unread count for the other user in all related conversations
        related_conversations = Conversation.query.filter(
            and_(
                ((Conversation.resident_id == current_user.id) & (Conversation.employer_id == other_user_id)) |
                ((Conversation.resident_id == other_user_id) & (Conversation.employer_id == current_user.id))
            )
        ).all()
        
        for conv in related_conversations:
            conv.unread_count += 1
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message_id': message.id,
            'conversation_id': most_recent_conversation.id
        })
        
    except Exception as e:
        current_app.logger.error(f"Error sending message: {str(e)}")
        return jsonify({'error': 'Failed to send message'}), 500

@api_bp.route('/users/online-status')
@login_required
def get_online_status():
    """Get online status for all users"""
    try:
        users = User.query.all()
        online_status = {}
        
        for user in users:
            online_status[user.id] = {
                'is_online': user.is_online(),
                'last_activity': user.get_last_activity().isoformat() if user.get_last_activity() else None
            }
        
        return jsonify(online_status)
        
    except Exception as e:
        current_app.logger.error(f"Error fetching online status: {str(e)}")
        return jsonify({'error': 'Failed to fetch online status'}), 500

@api_bp.route('/users/activity', methods=['POST'])
@login_required
def update_user_activity():
    """Update user activity timestamp"""
    try:
        # Update or create user session
        session_id = request.headers.get('X-Session-ID', str(uuid.uuid4()))
        
        # First try to find existing session by session_id (not user_id + session_id)
        existing_session = UserSession.query.filter_by(session_id=session_id).first()
        
        if existing_session:
            # Update existing session
            existing_session.last_activity = datetime.utcnow()
            existing_session.is_online = True
            existing_session.ip_address = request.remote_addr
            existing_session.user_agent = request.headers.get('User-Agent')
        else:
            # Create new session
            new_session = UserSession(
                user_id=current_user.id,
                session_id=session_id,
                last_activity=datetime.utcnow(),
                is_online=True,
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent')
            )
            db.session.add(new_session)
        
        db.session.commit()
        
        return jsonify({'success': True})
        
    except Exception as e:
        current_app.logger.error(f"Error updating user activity: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Failed to update activity'}), 500

@api_bp.route('/users/offline', methods=['POST'])
@login_required
def set_user_offline():
    """Mark user as offline"""
    try:
        # Mark all sessions for this user as offline
        UserSession.query.filter_by(user_id=current_user.id).update({
            'is_online': False
        })
        db.session.commit()
        
        return jsonify({'success': True})
        
    except Exception as e:
        current_app.logger.error(f"Error setting user offline: {str(e)}")
        return jsonify({'error': 'Failed to set offline'}), 500

@api_bp.route('/users/search')
@login_required
def search_users():
    """Search for users by name or email"""
    try:
        query = request.args.get('q', '').strip()
        if not query or len(query) < 2:
            return jsonify({'users': []})
        
        users = User.query.filter(
            and_(
                (User.name.ilike(f"%{query}%") | User.email.ilike(f"%{query}%")),
                User.id != current_user.id
            )
        ).limit(10).all()
        
        user_data = []
        for user in users:
            photo_filename = None
            if user.role.value == 'resident':
                profile = ResidentProfile.query.filter_by(user_id=user.id).first()
                if profile:
                    photo_filename = profile.photo_filename
            elif user.role.value == 'employer':
                profile = EmployerProfile.query.filter_by(user_id=user.id).first()
                if profile:
                    photo_filename = profile.photo_filename
        
            user_data.append({
                'id': user.id,
                'name': user.name,
                'email': user.email,
                'role': user.role.value,
                'organization': user.organization,
                'photo_filename': photo_filename,
                'is_online': user.is_online()
            })
        
        return jsonify({'users': user_data})
        
    except Exception as e:
        current_app.logger.error(f"Error searching users: {str(e)}")
        return jsonify({'error': 'Failed to search users'}), 500

@api_bp.route('/conversations/start-direct', methods=['POST'])
@login_required
def start_direct_conversation():
    """Start a direct conversation with another user"""
    try:
        data = request.get_json()
        other_user_id = data.get('user_id')
        
        if not other_user_id:
            return jsonify({'error': 'Missing user_id'}), 400
        
        if other_user_id == current_user.id:
            return jsonify({'error': 'Cannot start conversation with yourself'}), 400
        
        other_user = User.query.get(other_user_id)
        if not other_user:
            return jsonify({'error': 'User not found'}), 404
        
        # Check if conversation already exists (including opportunity-based ones)
        existing_convo = Conversation.query.filter(
            and_(
                ((Conversation.resident_id == current_user.id) & (Conversation.employer_id == other_user_id)) |
                ((Conversation.resident_id == other_user_id) & (Conversation.employer_id == current_user.id))
            )
        ).first()
        
        if existing_convo:
            return jsonify({
                'conversation_id': existing_convo.id,
                'message': 'Conversation already exists'
            })
        
        # Create new direct conversation
        if current_user.role.value == 'resident':
            new_convo = Conversation(
                resident_id=current_user.id,
                employer_id=other_user_id
            )
        else:
            new_convo = Conversation(
                resident_id=other_user_id,
                employer_id=current_user.id
            )
        
        db.session.add(new_convo)
        db.session.commit()
        
        return jsonify({
            'conversation_id': new_convo.id,
            'message': 'Conversation started successfully'
        })
        
    except Exception as e:
        current_app.logger.error(f"Error starting direct conversation: {str(e)}")
        return jsonify({'error': 'Failed to start conversation'}), 500


