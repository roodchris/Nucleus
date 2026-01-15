#!/usr/bin/env python3
"""
Script to generate realistic forum posts, comments, and votes
Creates fake users and organic-looking conversations over the past 3 months
"""

import os
import sys
import random
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash

# Add the app directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.models import db, User, ForumPost, ForumComment, ForumVote, ForumCategory, UserRole

# Silly usernames for fake users
FAKE_USER_NAMES = [
    "CT_Scans_My_Soul", "CodeBlueAndTired", "Stethoscope_Whisperer", "The_Intern_Struggle", "Epic_Fails_Daily",
    "CoffeeIV_Drip", "Pager_Nightmares", "Rounds_Of_Hell", "Sleep_Is_A_Myth", "Attending_Anxiety",
    "Scrub_Life_4Ever", "WhiteCoat_Blues", "MedSchool_Regrets", "Call_Room_Crawler", "DNR_My_Life",
    "Trauma_Bonded", "ICU_See_You", "Surgical_Struggles", "Radiology_Rad", "Pathology_Pathos",
    "Anesthesia_Amnesia", "Psych_Ward_Wanderer", "EM_Chaos_Queen", "Peds_Pain", "OB_GYN_Oh_No",
    "Ortho_Bro_Energy", "Derm_Life_Goals", "Cardio_Crushed", "Neuro_Nightmare", "GI_Gone_Wrong"
]

# Medical specialties for posts
SPECIALTIES = [
    "Radiology", "Internal Medicine", "Emergency Medicine", "Surgery", "Pediatrics",
    "Anesthesiology", "Psychiatry", "Family Medicine", "Neurology", "Cardiology",
    "Orthopedic Surgery", "Dermatology", "OB/GYN", "Pathology", "Urology"
]

# Forum post templates - realistic, casual, sometimes humorous
FORUM_POSTS = [
    {
        "title": "Anyone else getting absolutely destroyed by overnight call?",
        "content": "yo just got off a 28hr shift and i'm dead. had 3 codes, 2 traumas, felt like 47 consults. coffee machine broke at 3am. pretty sure i saw my soul leave my body around hour 24. idk if i'm even alive rn or if this is just purgatory. send help. or don't. might be too far gone 😭",
        "category": ForumCategory.GENERAL,
        "specialty": "Emergency Medicine"
    },
    {
        "title": "Interesting case: 45yo M with chest pain",
        "content": "had this dude come in with chest pain, ekg looked fine at first. but something felt off so i ordered a CT and boom - massive PE. ekg actually had subtle signs we missed. always trust your gut even when workup looks normal. anyone else had this? also my attending said 'probably just anxiety' - thanks for the confidence boost bro",
        "category": ForumCategory.GENERAL,
        "specialty": "Emergency Medicine"
    },
    {
        "title": "New study on AI in radiology - thoughts?",
        "content": "just read that new paper about AI detecting fractures. 98% sensitivity which is wild. are we all getting replaced by robots? 😅 but fr how are people using this in practice? at this point the AI probably has better work-life balance than me. at least it doesn't deal with epic crashing every 5 min",
        "category": ForumCategory.GENERAL,
        "specialty": "Radiology"
    },
    {
        "title": "Salary negotiation tips?",
        "content": "got my first attending offer. base is 350k but feel like i should negotiate. what's everyone's experience? do you ask for more base, better benefits, or both? also is it normal to feel greedy?",
        "category": ForumCategory.SALARY,
        "specialty": "Internal Medicine"
    },
    {
        "title": "Private practice vs academic - help me decide",
        "content": "torn between private practice (better pay, more autonomy) vs staying academic (research, teaching). anyone made the switch and regretted it? or vice versa?",
        "category": ForumCategory.JOB_ADVICE,
        "specialty": "Radiology"
    },
    {
        "title": "The most ridiculous consult I've received this week",
        "content": "got a consult at 2am: 'patient has headache. please evaluate.' no imaging, no neuro exam, just... headache. not even mad, impressed by the audacity tbh. what's your worst consult? i got paged at 3am once for 'patient seems sad' - like bro we're all sad at 3am that's just called being human",
        "category": ForumCategory.GENERAL,
        "specialty": "Neurology"
    },
    {
        "title": "How do you maintain work-life balance?",
        "content": "fr asking. feel like i'm drowning. between residency, studying for boards, and trying to have a life, something's gotta give. what are your strategies? my current strategy is crying in the call room and pretending my coffee is a margarita. not working great",
        "category": ForumCategory.GENERAL,
        "specialty": None
    },
    {
        "title": "Fellowship application season is here",
        "content": "starting to work on fellowship apps and already stressed. how many programs did everyone apply to? is it normal to feel not competitive enough even though PD says you're fine?",
        "category": ForumCategory.FELLOWSHIP,
        "specialty": "Internal Medicine"
    },
    {
        "title": "Step 3 studying while on rotations - possible?",
        "content": "trying to study for step 3 while on a busy rotation and struggling. anyone have tips for efficient studying? or should i just take dedicated time?",
        "category": ForumCategory.STUDYING,
        "specialty": None
    },
    {
        "title": "Radiology residents - how's your call schedule?",
        "content": "our program just changed call schedule and it's... not great. wondering what other programs are doing. q4, q5, q6? how many weekends?",
        "category": ForumCategory.RESIDENCY_ADVICE,
        "specialty": "Radiology"
    },
    {
        "title": "Patient asked me if I googled their symptoms",
        "content": "had a patient straight up ask if i was googling their diagnosis. was actually looking up a drug interaction but now questioning everything. how do you handle this? was like 'no checking uptodate' but tbh sometimes i do google things and i'm not ashamed. we're not walking encyclopedias",
        "category": ForumCategory.GENERAL,
        "specialty": "Family Medicine"
    },
    {
        "title": "Compensation data - is $400k reasonable for radiology?",
        "content": "got an offer in mid-size city, 400k base plus productivity. seems decent but don't have great benchmarks. what are people seeing out there?",
        "category": ForumCategory.SALARY,
        "specialty": "Radiology"
    },
    {
        "title": "The EMR is trying to kill me",
        "content": "spent 45 min trying to order a simple lab today because epic decided to have a meltdown. why do we make everything so complicated? pretty sure epic was designed by someone who's never worked in a hospital. or maybe they did and this is their revenge. either way i'm convinced it's sentient and hates us all",
        "category": ForumCategory.GENERAL,
        "specialty": None
    },
    {
        "title": "Interesting pediatric case - 8yo with abdominal pain",
        "content": "8yo with 2 days abdominal pain, no fever, labs normal. CT showed appendicitis but super subtle. kid was a champ though. anyone else find peds cases more challenging diagnostically?",
        "category": ForumCategory.GENERAL,
        "specialty": "Pediatrics"
    },
    {
        "title": "Should I do a research year?",
        "content": "thinking about taking a research year to boost fellowship apps. is it worth it? or should i just apply and see what happens?",
        "category": ForumCategory.FELLOWSHIP,
        "specialty": "Surgery"
    },
    {
        "title": "The attending who changed my perspective",
        "content": "had this amazing attending who actually taught instead of just pimping. made me realize what kind of doc i want to be. anyone have similar experiences? need more mentors like this",
        "category": ForumCategory.RESIDENCY_ADVICE,
        "specialty": None
    },
    {
        "title": "Moonlighting opportunities - worth it?",
        "content": "got offered a moonlighting gig, 150/hr. sounds great but already exhausted. is the extra money worth the burnout? what's everyone's experience?",
        "category": ForumCategory.JOB_ADVICE,
        "specialty": None
    },
    {
        "title": "New guidelines for stroke management",
        "content": "just read updated stroke guidelines. window for thrombectomy keeps expanding. are people actually following these in practice? seems like every hospital does things differently",
        "category": ForumCategory.GENERAL,
        "specialty": "Neurology"
    },
    {
        "title": "How to deal with difficult attendings",
        "content": "there's this one attending who makes rounds miserable. always pimping on irrelevant details, belittling residents. how do you all handle this? just grin and bear it? i've started keeping a mental list of all the times they've been wrong. it's getting long. petty? maybe. therapeutic? absolutely",
        "category": ForumCategory.RESIDENCY_ADVICE,
        "specialty": None
    },
    {
        "title": "The case that keeps me up at night",
        "content": "had a patient a few months ago i still think about. missed something subtle, bad outcome. know we all make mistakes but this one hit different. how do you process these? therapist says 'practice self-compassion' but tbh i'll probably just carry this to my grave. it's fine. everything's fine",
        "category": ForumCategory.GENERAL,
        "specialty": "Emergency Medicine"
    },
    {
        "title": "Board prep - UWorld vs other resources?",
        "content": "starting to study for boards. everyone says uworld is gold standard but expensive. are there other good resources? or should i just bite the bullet?",
        "category": ForumCategory.STUDYING,
        "specialty": None
    },
    {
        "title": "Rural vs urban practice - pros and cons?",
        "content": "got offers in both. rural pays more and more autonomous but worried about isolation and resources. urban has better support but more bureaucracy. help me think through this",
        "category": ForumCategory.JOB_ADVICE,
        "specialty": "Internal Medicine"
    },
    {
        "title": "The most satisfying diagnosis you've made",
        "content": "had a patient with weird symptoms no one could figure out. did some deep digging, found rare diagnosis, patient got better. felt like house md for a day. what's your best diagnostic win?",
        "category": ForumCategory.GENERAL,
        "specialty": None
    },
    {
        "title": "Residency program red flags",
        "content": "interviewing for residency and trying to figure out what to look for. what are the red flags that made you nope out of a program?",
        "category": ForumCategory.RESIDENCY_ADVICE,
        "specialty": None
    },
    {
        "title": "How much should I be saving as a resident?",
        "content": "making resident salary, trying to figure out finances. should i be maxing out retirement accounts? or just trying to survive? financial advisors keep giving conflicting advice",
        "category": ForumCategory.SALARY,
        "specialty": None
    },
    {
        "title": "The evolution of medical education",
        "content": "was talking to an older attending about how training changed. less autonomy, more documentation, more oversight. is this better or worse? are we training better doctors or just more compliant ones?",
        "category": ForumCategory.GENERAL,
        "specialty": None
    },
    {
        "title": "Interesting surgical case - laparoscopic vs open",
        "content": "had a debate with attending about approach. i thought laparoscopic, they wanted open. ended up doing open and it was right call. learning to trust experience vs what literature says",
        "category": ForumCategory.GENERAL,
        "specialty": "Surgery"
    },
    {
        "title": "Dealing with patient families",
        "content": "had a family member today who was... challenging. demanding, rude, questioning everything. how do you all maintain professionalism when families are difficult? perfected the fake smile while internally screaming. it's a skill. sometimes wonder if they know i'm one bad day away from walking out",
        "category": ForumCategory.GENERAL,
        "specialty": None
    },
    {
        "title": "The future of radiology",
        "content": "with AI advancing so fast, where do you see radiology in 10 years? are we all getting replaced? or will it just change how we practice?",
        "category": ForumCategory.GENERAL,
        "specialty": "Radiology"
    },
    {
        "title": "Work-life balance in different specialties",
        "content": "curious about lifestyle differences. know derm and rads are supposed to be lifestyle-friendly but what's the reality? what about other specialties?",
        "category": ForumCategory.JOB_ADVICE,
        "specialty": None
    }
]

# Comment templates - casual texting style, locker room talk
COMMENT_TEMPLATES = [
    "ugh been there. worst is when you finally get to sleep and then get paged 10 min later. sleep deprivation is torture fr",
    "so relatable. had similar case last month still haunts me at 3am. thanks for that",
    "lol this made my day. audacity of some consults is wild. got paged once for 'patient seems tired' - like join the club bro",
    "can confirm. source: also exhausted and questioning life choices daily",
    "this is why i chose [specialty]. lifestyle worth the pay cut. jk still broke and tired",
    "feel this in my soul. struggle is real and my soul is tired",
    "this is the content i'm here for. more dark humor less toxic positivity",
    "same experience. frustrating but you're not alone. solidarity bro",
    "so true. need more discussions where we can be honest about how much this sucks",
    "pretty sure EMR was designed by someone who's never worked in a hospital. or they did and this is revenge",
    "exactly what i needed to hear. thanks for validating my existential crisis",
    "disagree but respect your take. here's why i'm wrong and you're right...",
    "hot take and i'm here for it. more chaos less order",
    "following. interested to see how many of us are actually okay (spoiler: none)",
    "this is why i love this community. finally people who get it",
    "saving this. so much good info and also so much pain",
    "kind of case that makes medicine interesting and also makes me want to quit",
    "had similar experience. validating to hear others go through this too even though i wish none of us had to",
    "great reminder we're all just trying our best and sometimes that's not enough. cool cool cool",
    "going through something similar. this helps or at least makes me feel less alone",
    "well said. couldn't agree more and also i'm tired",
    "not sure i agree but appreciate the perspective. also i'm probably wrong",
    "reality check i needed today. thanks i hate it",
    "following. curious what others think but also scared",
    "glad i found this forum. finally people who understand",
    "exactly my experience. thanks for putting it into words",
    "fact that this is so relatable is both comforting and concerning",
    "pretty sure we're all one bad shift away from breakdown. this confirms it",
    "kind of honesty we need. less 'medicine is a calling' more 'medicine is hard and sometimes i want to quit'",
    "can't relate but fascinating. also scared for when i will"
]

def generate_comment_content(post_title, post_content, specialty=None):
    """Generate realistic comment content based on the post"""
    # Sometimes use templates, sometimes generate contextual responses
    if random.random() < 0.4:
        return random.choice(COMMENT_TEMPLATES)
    
    # Generate contextual responses - casual texting style
    contextual_responses = {
        "call": [
            "coffee machine breaking is final boss of overnight call. started bringing my own instant coffee and will to live",
            "28 hours? brutal. program caps at 24 but still feels like forever. time doesn't work same way in hospital",
            "feel this. had similar night last week. post-call day is worst. still recovering physically and emotionally",
            "at hour 26 started seeing things. pretty sure had conversation with wall. wall was more helpful than some consults"
        ],
        "case": [
            "great catch. always trust your gut. had similar case where workup was normal but something felt off. trusted gut, saved life, still have nightmares",
            "good reminder. sometimes subtle signs are most important. also sometimes we miss them and people die. no pressure",
            "interesting case. thanks for sharing. these stick with you, both good catches and ones that got away"
        ],
        "salary": [
            "solid offer depending on location. definitely negotiate - worst they say is no. if they say no you probably don't want to work there anyway",
            "don't feel greedy. negotiation expected. ask for both base and benefits. also ask for therapist because you'll need one",
            "negotiated first offer got extra 20k. always worth asking. worst they do is laugh at you which happens anyway"
        ],
        "balance": [
            "so hard. been trying to set boundaries but easier said than done. boundaries currently: don't die, try to sleep sometimes, cry in private",
            "started blocking out time for myself. even if just 30 min it helps. those 30 min are sacred. touch them and die",
            "eternal struggle. don't have answers but you're not alone. we're all drowning together which is somehow comforting?"
        ],
        "consult": [
            "lol got consult once for 'patient is sad.' that's it. just sad. me too bro",
            "worst is when they consult at 3am for something going on for weeks. audacity is wild",
            "got consult for 'patient has headache' at 2am. no neuro exam no imaging. just headache. still not over it"
        ]
    }
    
    # Try to match context
    post_lower = (post_title + " " + post_content).lower()
    for key, responses in contextual_responses.items():
        if key in post_lower:
            return random.choice(responses)
    
    # Default contextual response - casual texting
    return random.choice([
        "really helpful thanks for sharing. also i'm tired",
        "going through something similar. this helps or at least makes me feel less alone",
        "great post. following for more discussion and pain",
        "exactly what i needed to hear today. thanks i hate it",
        "thanks for insight. hadn't thought about it this way now questioning everything",
        "kind of honesty we need. less toxic positivity more real talk about how hard this is",
        "preach. all of this. every word",
        "felt this in my bones. my tired bones"
    ])

def create_fake_users(app):
    """Create fake user accounts"""
    print("Creating fake users...")
    users = []
    
    # Check if fake users already exist
    existing_count = User.query.filter(User.email.like("forum_user_%@example.com")).count()
    if existing_count > 0:
        print(f"⚠️  Found {existing_count} existing fake users. Reusing them...")
        users = User.query.filter(User.email.like("forum_user_%@example.com")).all()
        return users
    
    for i, name in enumerate(FAKE_USER_NAMES):
        # Check if user already exists
        email = f"forum_user_{i+1}@example.com"
        existing = User.query.filter_by(email=email).first()
        if existing:
            users.append(existing)
            continue
        
        user = User(
            email=email,
            password_hash=generate_password_hash("fake_password_123"),  # Dummy password
            name=name,
            role=random.choice([UserRole.RESIDENT, UserRole.EMPLOYER]),
            created_at=datetime.utcnow() - timedelta(days=random.randint(90, 180))  # Created 3-6 months ago
        )
        db.session.add(user)
        users.append(user)
    
    db.session.commit()
    print(f"✅ Created {len(users)} fake users")
    return users

def generate_forum_content(app, users):
    """Generate forum posts, comments, and votes"""
    print("\nGenerating forum posts...")
    
    # Check if posts already exist (prevent duplicate runs)
    existing_posts = ForumPost.query.filter(
        ForumPost.author_id.in_([u.id for u in users])
    ).count()
    
    if existing_posts > 0:
        print(f"⚠️  Found {existing_posts} existing forum posts from fake users.")
        print("⚠️  Continuing anyway - this will add more posts to the database.")
        print("⚠️  If you want to start fresh, delete existing posts first.\n")
    
    # Calculate date range (past 3 months)
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=90)
    
    posts = []
    all_comments = []
    
    # Create 30 posts spread over 3 months
    for i, post_data in enumerate(FORUM_POSTS):
        # Distribute posts over 3 months (more recent posts slightly more common)
        days_ago = random.randint(0, 90)
        # Weight towards more recent posts
        if random.random() < 0.3:
            days_ago = random.randint(0, 30)  # 30% in last month
        
        post_date = end_date - timedelta(days=days_ago)
        author = random.choice(users)
        
        post = ForumPost(
            author_id=author.id,
            title=post_data["title"],
            content=post_data["content"],
            category=post_data["category"],
            specialty=post_data.get("specialty"),
            created_at=post_date,
            updated_at=post_date,
            is_pinned=False,
            is_locked=False
        )
        db.session.add(post)
        posts.append(post)
    
    db.session.commit()
    print(f"✅ Created {len(posts)} forum posts")
    
    # Create comments for each post
    print("\nGenerating comments and replies...")
    
    for post in posts:
        # Number of comments per post (weighted - some posts get more engagement)
        num_comments = random.choices(
            [0, 1, 2, 3, 4, 5, 6, 7, 8],
            weights=[5, 10, 15, 20, 20, 15, 10, 4, 1]
        )[0]
        
        if num_comments == 0:
            continue
        
        # Create top-level comments
        top_level_comments = []
        for j in range(num_comments):
            # Comments appear within a few days of the post (most within 1-2 days)
            comment_delay = random.randint(0, 7)
            if random.random() < 0.7:  # 70% within 1 day
                comment_delay = random.randint(0, 1)
            
            comment_date = post.created_at + timedelta(
                days=comment_delay // 1,
                hours=random.randint(0, 23),
                minutes=random.randint(0, 59)
            )
            
            comment_author = random.choice(users)
            comment_content = generate_comment_content(
                post.title, post.content, post.specialty
            )
            
            comment = ForumComment(
                post_id=post.id,
                author_id=comment_author.id,
                parent_comment_id=None,
                content=comment_content,
                created_at=comment_date,
                updated_at=comment_date,
                is_edited=False,
                is_deleted=False
            )
            db.session.add(comment)
            top_level_comments.append(comment)
            all_comments.append(comment)
        
        db.session.commit()
        
        # Create nested replies (30% of comments get replies)
        for comment in top_level_comments:
            if random.random() < 0.3:  # 30% chance of replies
                num_replies = random.choices([1, 2, 3], weights=[60, 30, 10])[0]
                
                for k in range(num_replies):
                    # Replies appear within hours/days of the parent comment
                    reply_delay_hours = random.randint(1, 48)
                    reply_date = comment.created_at + timedelta(
                        hours=reply_delay_hours,
                        minutes=random.randint(0, 59)
                    )
                    
                    reply_author = random.choice(users)
                    # Replies are shorter, casual texting style
                    reply_content = random.choice([
                        "this. exactly this. my soul felt this",
                        "couldn't agree more. also i'm tired",
                        "had same experience. was terrible thanks for reminding me",
                        "so true. why do we do this to ourselves",
                        "thanks for sharing. validating and also depressing",
                        "going through this right now too. send help. or don't probably beyond saving",
                        "helpful thanks. also i hate it",
                        "same here. frustrating and questioning everything",
                        "feel this so much. therapist going to hear about this",
                        "reality check i needed. thanks i hate it",
                        "preach. all of this. every word",
                        "yep. this is my life now. cool cool cool",
                        "felt this in my bones. my tired bones",
                        "same energy. different day. still suffering",
                        "content i'm here for. more pain please",
                        "fr",
                        "mood",
                        "big mood",
                        "same",
                        "relatable",
                        "too real",
                        "ouch",
                        "felt that"
                    ])
                    
                    reply = ForumComment(
                        post_id=post.id,
                        author_id=reply_author.id,
                        parent_comment_id=comment.id,
                        content=reply_content,
                        created_at=reply_date,
                        updated_at=reply_date,
                        is_edited=False,
                        is_deleted=False
                    )
                    db.session.add(reply)
                    all_comments.append(reply)
        
        db.session.commit()
    
    print(f"✅ Created {len(all_comments)} comments and replies")
    
    # Create votes for posts and comments
    print("\nGenerating votes...")
    vote_count = 0
    
    # Vote on posts (60-80% of posts get votes)
    for post in posts:
        if random.random() < 0.7:  # 70% of posts get votes
            num_voters = random.choices([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], 
                                       weights=[15, 15, 15, 15, 12, 10, 8, 5, 3, 2])[0]
            
            voters = random.sample(users, min(num_voters, len(users)))
            
            for voter in voters:
                # Most votes are upvotes (85%), some downvotes (15%)
                vote_type = "upvote" if random.random() < 0.85 else "downvote"
                
                # Vote appears after post creation
                vote_date = post.created_at + timedelta(
                    hours=random.randint(1, 72),
                    minutes=random.randint(0, 59)
                )
                
                vote = ForumVote(
                    user_id=voter.id,
                    post_id=post.id,
                    comment_id=None,
                    vote_type=vote_type,
                    created_at=vote_date
                )
                db.session.add(vote)
                vote_count += 1
    
    # Vote on comments (30-40% of comments get votes)
    for comment in all_comments:
        if random.random() < 0.35:  # 35% of comments get votes
            num_voters = random.choices([1, 2, 3, 4, 5], 
                                       weights=[40, 30, 20, 8, 2])[0]
            
            voters = random.sample(users, min(num_voters, len(users)))
            
            for voter in voters:
                # Most votes are upvotes (90%), some downvotes (10%)
                vote_type = "upvote" if random.random() < 0.9 else "downvote"
                
                # Vote appears after comment creation
                vote_date = comment.created_at + timedelta(
                    hours=random.randint(1, 48),
                    minutes=random.randint(0, 59)
                )
                
                vote = ForumVote(
                    user_id=voter.id,
                    post_id=None,
                    comment_id=comment.id,
                    vote_type=vote_type,
                    created_at=vote_date
                )
                db.session.add(vote)
                vote_count += 1
    
    db.session.commit()
    print(f"✅ Created {vote_count} votes")
    
    return posts, all_comments

def main():
    """Main function to generate forum content"""
    print("=" * 60)
    print("Generating Forum Content")
    print("=" * 60)
    
    app = create_app()
    
    with app.app_context():
        try:
            # Create fake users
            users = create_fake_users(app)
            
            # Generate forum content
            posts, comments = generate_forum_content(app, users)
            
            print("\n" + "=" * 60)
            print("✅ SUCCESS!")
            print("=" * 60)
            print(f"Created:")
            print(f"  - {len(users)} fake users")
            print(f"  - {len(posts)} forum posts")
            print(f"  - {len(comments)} comments and replies")
            print(f"\nAll content spread over the past 3 months")
            print("=" * 60)
            
        except Exception as e:
            print(f"\n❌ ERROR: {e}")
            import traceback
            traceback.print_exc()
            db.session.rollback()
            sys.exit(1)

if __name__ == "__main__":
    main()

