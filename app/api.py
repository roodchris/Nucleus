from flask import Blueprint, jsonify, request, current_app, Response
from flask_login import login_required, current_user
from app.models import Conversation, Message, User, ResidentProfile, EmployerProfile
from app import db
from sqlalchemy import desc, and_
from datetime import datetime
import uuid
import json
import time
from app.models import UserSession
from flask_mail import Message as MailMessage

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
                # Count unread messages from the other user to current user
                unread_count = Message.query.filter(
                    and_(
                        Message.conversation_id == conv.id,
                        Message.sender_id == other_user_id,
                        Message.is_read == False
                    )
                ).count()
            else:
                other_user_id = conv.resident_id
                other_user = conv.resident
                # Count unread messages from the other user to current user
                unread_count = Message.query.filter(
                    and_(
                        Message.conversation_id == conv.id,
                        Message.sender_id == other_user_id,
                        Message.is_read == False
                    )
                ).count()
            
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

@api_bp.route('/user/profile')
@login_required
def current_user_profile():
    """Get current user's profile information including photo"""
    try:
        current_user_photo = None
        if current_user.role.value == 'resident':
            from .models import ResidentProfile
            resident_profile = ResidentProfile.query.filter_by(user_id=current_user.id).first()
            if resident_profile and resident_profile.photo_filename:
                current_user_photo = resident_profile.photo_filename
        elif current_user.role.value == 'employer':
            from .models import EmployerProfile
            employer_profile = EmployerProfile.query.filter_by(user_id=current_user.id).first()
            if employer_profile and employer_profile.photo_filename:
                current_user_photo = employer_profile.photo_filename
        
        return jsonify({
            'id': current_user.id,
            'name': current_user.name,
            'role': current_user.role.value,
            'photo_filename': current_user_photo
        })
        
    except Exception as e:
        current_app.logger.error(f"Error fetching current user profile: {str(e)}")
        return jsonify({'error': 'Failed to fetch profile'}), 500


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
                    'conversation_id': conv.id,
                    'is_read': msg.is_read
                })
        
        # Sort all messages by timestamp
        all_messages.sort(key=lambda x: x['timestamp'] or '')
        
        # Mark all messages from the other user as read in all related conversations
        for conv in related_conversations:
            # Mark messages from other user as read
            unread_messages = Message.query.filter(
                and_(
                    Message.conversation_id == conv.id,
                    Message.sender_id == other_user_id,
                    Message.is_read == False
                )
            ).all()
            
            for msg in unread_messages:
                msg.is_read = True
            
            # Reset unread count for this conversation
            conv.unread_count = 0
        
        db.session.commit()
        
        # Get profile photo for other user
        other_user_photo = None
        if other_user.role.value == 'resident':
            from .models import ResidentProfile
            resident_profile = ResidentProfile.query.filter_by(user_id=other_user.id).first()
            if resident_profile and resident_profile.photo_filename:
                other_user_photo = resident_profile.photo_filename
        elif other_user.role.value == 'employer':
            from .models import EmployerProfile
            employer_profile = EmployerProfile.query.filter_by(user_id=other_user.id).first()
            if employer_profile and employer_profile.photo_filename:
                other_user_photo = employer_profile.photo_filename
        
        return jsonify({
            'messages': all_messages,
            'other_user': {
                'id': other_user.id,
                'name': other_user.name,
                'role': other_user.role.value,
                'photo_filename': other_user_photo
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
            # Increment unread count for the other user
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


# Store active SSE connections
active_connections = {}

@api_bp.route('/messages/stream')
def message_stream():
    """Server-Sent Events endpoint for real-time message updates"""
    def event_stream():
        # Create a unique connection ID
        connection_id = str(uuid.uuid4())
        
        # For EventSource, we need to handle authentication differently
        # Try to get user from session or current_user
        user_id = None
        
        # First try current_user (if available)
        if current_user and current_user.is_authenticated:
            user_id = current_user.id
        else:
            # Try session-based authentication
            from flask import session
            user_id = session.get('_user_id')
            if user_id:
                # Verify user exists
                user = User.query.get(user_id)
                if not user:
                    user_id = None
        
        if not user_id:
            yield f"data: {json.dumps({'error': 'User not authenticated'})}\n\n"
            return
            
        active_connections[connection_id] = {
            'user_id': user_id,
            'last_check': datetime.utcnow()
        }
        
        try:
            # Send initial connection confirmation
            yield f"data: {json.dumps({'type': 'connected', 'message': 'EventSource connected successfully'})}\n\n"
            
            while True:
                try:
                    # Check for new messages
                    last_check = active_connections[connection_id]['last_check']
                    
                    # Get conversations where user is involved
                    conversations = Conversation.query.filter(
                        (Conversation.resident_id == user_id) | 
                        (Conversation.employer_id == user_id)
                    ).all()
                    
                    conversation_ids = [conv.id for conv in conversations]
                    
                    # Get new messages since last check
                    new_messages = Message.query.filter(
                        and_(
                            Message.conversation_id.in_(conversation_ids),
                            Message.sender_id != user_id,  # Only messages from others
                            Message.created_at > last_check
                        )
                    ).order_by(Message.created_at.desc()).all()
                    
                    if new_messages:
                        # Get updated conversation data
                        updated_conversations = []
                        for conv in conversations:
                            # Get the other user
                            if conv.resident_id == user_id:
                                other_user = conv.employer
                            else:
                                other_user = conv.resident
                            
                            # Get unread count - count messages from other user that are unread by current user
                            other_user_id = conv.employer_id if conv.resident_id == user_id else conv.resident_id
                            unread_count = Message.query.filter(
                                and_(
                                    Message.conversation_id == conv.id,
                                    Message.sender_id == other_user_id,
                                    Message.is_read == False
                                )
                            ).count()
                            
                            updated_conversations.append({
                                'id': conv.id,
                                'other_user': {
                                    'id': other_user.id,
                                    'name': other_user.name,
                                    'role': other_user.role.value
                                },
                                'last_message': {
                                    'content': conv.last_message.body if conv.last_message else '',
                                    'timestamp': conv.last_message.created_at.isoformat() if conv.last_message else None,
                                    'sender_id': conv.last_message.sender_id if conv.last_message else None
                                },
                                'unread_count': unread_count,
                                'updated_at': conv.updated_at.isoformat() if conv.updated_at else None
                            })
                        
                        # Send the update
                        data = {
                            'type': 'new_messages',
                            'conversations': updated_conversations,
                            'new_messages_count': len(new_messages),
                            'timestamp': datetime.utcnow().isoformat()
                        }
                        
                        yield f"data: {json.dumps(data)}\n\n"
                    else:
                        # Send heartbeat to keep connection alive
                        yield f"data: {json.dumps({'type': 'heartbeat', 'timestamp': datetime.utcnow().isoformat()})}\n\n"
                    
                    # Update last check time
                    active_connections[connection_id]['last_check'] = datetime.utcnow()
                    
                    # Wait 5 seconds before next check
                    time.sleep(5)
                    
                except Exception as e:
                    current_app.logger.error(f"Error in EventSource loop: {str(e)}")
                    yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
                    break
                
        except GeneratorExit:
            # Clean up connection when client disconnects
            if connection_id in active_connections:
                del active_connections[connection_id]
        except Exception as e:
            current_app.logger.error(f"Error in message stream: {str(e)}")
            # Clean up connection on error
            if connection_id in active_connections:
                del active_connections[connection_id]
    
    return Response(event_stream(), mimetype='text/event-stream', headers={
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Cache-Control'
    })

@api_bp.route('/feedback', methods=['POST'])
def submit_feedback():
    """Submit user feedback, bug reports, or feature requests"""
    try:
        data = request.get_json()
        
        if not data or 'message' not in data:
            return jsonify({'error': 'Message is required'}), 400
        
        message = data['message'].strip()
        if not message:
            return jsonify({'error': 'Message cannot be empty'}), 400
        
        if len(message) > 1000:
            return jsonify({'error': 'Message too long (max 1000 characters)'}), 400
        
        # Get user info if authenticated
        user_info = "Anonymous user"
        if current_user.is_authenticated:
            user_info = f"{current_user.name} ({current_user.email})"
        
        # Get additional context
        page = data.get('page', 'Unknown page')
        user_agent = data.get('user_agent', 'Unknown browser')
        
        # Create email content
        subject = f"Feedback from Nucleus - {page}"
        
        email_body = f"""
New feedback submitted on Nucleus:

User: {user_info}
Page: {page}
Browser: {user_agent}
Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}

Message:
{message}

---
This feedback was submitted through the Nucleus website feedback form.
        """.strip()
        
        # Send email
        try:
            from flask_mail import Mail
            mail = Mail(current_app)
            
            # Check if email is configured
            if not current_app.config.get('MAIL_USERNAME') or not current_app.config.get('MAIL_PASSWORD'):
                current_app.logger.warning("Email not configured, storing feedback locally")
                # Store feedback in database or log file as fallback
                current_app.logger.info(f"FEEDBACK: {email_body}")
                return jsonify({
                    'success': True,
                    'message': 'Feedback received! (Email not configured)'
                })
            
            msg = MailMessage(
                subject=subject,
                recipients=['radnucleus@gmail.com'],
                body=email_body,
                sender=current_app.config.get('MAIL_USERNAME', 'noreply@nucleus.com')
            )
            
            mail.send(msg)
            
            return jsonify({
                'success': True,
                'message': 'Feedback submitted successfully'
            })
            
        except Exception as email_error:
            current_app.logger.error(f"Failed to send feedback email: {email_error}")
            # Log the feedback as fallback
            current_app.logger.info(f"FEEDBACK FALLBACK: {email_body}")
            return jsonify({
                'error': 'Email service unavailable, but feedback was logged. Please try again later.'
            }), 500
            
    except Exception as e:
        current_app.logger.error(f"Feedback submission error: {e}")
        return jsonify({
            'error': 'An unexpected error occurred. Please try again.'
        }), 500


