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

# Post-specific meaningful comments - each post gets relevant, insightful comments
POST_SPECIFIC_COMMENTS = {
    "Anyone else getting absolutely destroyed by overnight call?": [
        "our program caps at 24hrs but honestly feels the same. the post-call delirium is real. started keeping a log of weird things i do post-call and it's... concerning",
        "28hrs is insane. we do q4 call and by day 3 i'm basically a zombie. coffee machine breaking at 3am is the final boss fr",
        "had a 30hr once during intern year. hallucinated that the walls were talking to me. attending sent me home early which was nice but also terrifying",
        "the worst part is when you finally get to sleep and your pager goes off 10 min later. your brain just breaks at that point"
    ],
    "Interesting case: 45yo M with chest pain": [
        "good catch on the PE. those subtle ekg changes are easy to miss. had similar case where initial trop was normal but something felt off - ended up being nstemi",
        "always trust your gut. had a patient with 'anxiety' chest pain that was actually aortic dissection. attending was not happy when i ordered the CT but patient lived",
        "pe can be sneaky. we had one where d-dimer was negative but still had massive PE. sometimes the workup lies to you",
        "the anxiety dismissal is so common. had attending tell me 'it's just panic' on a patient who ended up having takotsubo. trust your instincts"
    ],
    "New study on AI in radiology - thoughts?": [
        "we're using AI for chest xrays now. catches things we miss but also has false positives. still need human oversight but it's getting scary good",
        "98% sensitivity is wild. but what about specificity? we tried AI for fractures and it flagged every single thing. had to turn sensitivity down",
        "i think AI will change how we practice but not replace us. more like a really good second read. the liability question is interesting though",
        "our hospital just got AI for stroke detection. it's actually pretty helpful for overnight when there's no neuro attending. but still makes me nervous"
    ],
    "Salary negotiation tips?": [
        "negotiated my first offer from 320k to 360k. asked for more base, better retirement match, and extra pto. got all of it. always ask",
        "don't feel greedy - it's expected. i asked for 50k more and they met me halfway. worst case they say no and you negotiate other stuff",
        "negotiate everything: base, productivity bonus, sign-on, relocation, pto, cme money. they expect it. my recruiter told me to ask for more",
        "got an extra 30k just by asking. also negotiated 4 weeks pto instead of 3. if you don't ask you don't get"
    ],
    "Private practice vs academic - help me decide": [
        "made the switch from academic to private. pay is way better but miss teaching. also miss the research opportunities. but my bank account doesn't",
        "stayed academic. pay is less but i love teaching residents. also get to do research which i couldn't in private. depends what you value",
        "private practice here. autonomy is great but miss the academic environment. also miss having residents to do scut work. but money is nice",
        "did academic first then switched. academic was more intellectually stimulating but private pays way better. no right answer just what you prioritize"
    ],
    "The most ridiculous consult I've received this week": [
        "got one at 4am: 'patient is constipated. please evaluate.' like... really? that's why you woke me up?",
        "had a consult for 'patient seems confused' at 2am. no neuro exam, no labs, nothing. just... seems confused. in a hospital. at 2am. shocking",
        "got paged for 'patient has rash' at 3am. no description, no exam, just... rash. turned out to be bed sheets. actual bed sheets",
        "consulted at 1am for 'patient is sad.' that's it. just sad. i was also sad. we were all sad. welcome to 1am in a hospital"
    ],
    "How do you maintain work-life balance?": [
        "it's impossible tbh. i try to block out one day a week for myself but even that gets interrupted. boundaries don't exist in medicine",
        "started saying no to extra shifts. money is nice but my sanity is nicer. also started therapy which helps",
        "i don't. that's the honest answer. i'm drowning and something's gotta give but idk what. probably my relationships",
        "set hard boundaries with my program. no extra shifts, no staying late unless emergency. they weren't happy but i'm still here"
    ],
    "Fellowship application season is here": [
        "applied to 15 programs. got 8 interviews. it's stressful but you'll be fine. everyone feels not competitive enough",
        "applied to 20. got 12 interviews. the process is brutal but you'll match somewhere. just be yourself in interviews",
        "applied to 10, got 6 interviews. less is more if you're strategic. don't apply to places you wouldn't actually go",
        "the anxiety is normal. everyone feels like they're not good enough. your PD wouldn't let you apply if you weren't competitive"
    ],
    "Step 3 studying while on rotations - possible?": [
        "did it during a lighter rotation. studied 1-2 hours a day for 3 months. passed comfortably. it's doable but sucks",
        "took dedicated time. couldn't focus while on rotations. worth it to just take the time and get it done",
        "studied during night float. lots of downtime. passed first try. depends on your rotation schedule",
        "did uworld questions during lunch breaks and after work. passed but barely. would recommend dedicated time if possible"
    ],
    "Radiology residents - how's your call schedule?": [
        "q4 call, 8 weekends a year. it's brutal but manageable. some programs do q5 which is way better",
        "q5 call, 6 weekends. changed from q4 last year and it's so much better. still tired but less dead",
        "q6 call, 4 weekends. program is pretty chill. know some programs doing q3 which is insane",
        "q4 call, 10 weekends. it's a lot. thinking about switching programs but don't want to restart"
    ],
    "Patient asked me if I googled their symptoms": [
        "happens all the time. i just say 'checking uptodate' which is technically true. sometimes i do google things and i'm not ashamed",
        "had this happen. was actually looking up drug interaction but now they think i'm incompetent. thanks patient",
        "i straight up tell them sometimes i google things. we're not walking encyclopedias. they usually appreciate the honesty",
        "just say 'consulting medical literature' which sounds professional. we all google things, it's fine"
    ],
    "Compensation data - is $400k reasonable for radiology?": [
        "depends on location. in midwest that's solid. on coasts might be low. also depends on productivity structure",
        "400k base is decent. what's the productivity bonus? that's where the real money is. know people making 500k+ with good productivity",
        "for mid-size city that's reasonable. know people making 350k and people making 600k. depends on volume and location",
        "sounds fair. negotiated mine from 380k to 420k. always ask for more. worst they say is no"
    ],
    "The EMR is trying to kill me": [
        "epic is the worst. spent 20 min trying to order tylenol yesterday. why is everything so complicated?",
        "switched from epic to cerner and it's somehow worse. all EMRs are terrible. pick your poison",
        "epic crashing is a feature not a bug. pretty sure it's designed to make us suffer. sentient and evil",
        "takes me 5 min to order a simple lab. used to take 30 seconds. 'improvements' my ass"
    ],
    "Interesting pediatric case - 8yo with abdominal pain": [
        "peds cases are harder. kids can't tell you what's wrong. had similar case where appendicitis was super subtle on imaging",
        "peds is challenging. same symptoms can be nothing or something serious. always err on side of caution",
        "kids are tough. had 6yo with appendicitis that looked normal on exam. CT saved the day. always trust your gut with kids",
        "peds appendicitis can be sneaky. labs normal, exam normal, but something feels off. good call on the CT"
    ],
    "Should I do a research year?": [
        "did one. helped my fellowship apps but also delayed my career by a year. worth it if you want competitive fellowship",
        "skipped it. matched to my top choice anyway. depends on how competitive you are and what you want",
        "research year was worth it. got 3 first author pubs and matched to dream program. but it's a year of your life",
        "didn't do one. matched fine. research year helps but not required for most programs. depends on your goals"
    ],
    "The attending who changed my perspective": [
        "had similar attending. actually taught instead of just pimping. made me want to be that kind of mentor",
        "those attendings are rare but they exist. had one who took time to explain things. changed how i approach teaching",
        "wish more attendings were like that. most just pimp and belittle. need more mentors who actually care",
        "had one who changed everything. showed me medicine can be collaborative not adversarial. trying to be like that now"
    ],
    "Moonlighting opportunities - worth it?": [
        "did it for 6 months. made good money but was exhausted. stopped because burnout wasn't worth it",
        "moonlighting is great money but kills you. did it for a year then stopped. my sanity is worth more",
        "150/hr is solid. did it for extra cash but had to stop. wasn't sustainable with residency",
        "moonlighting helped pay off loans but made me miserable. stopped after 3 months. not worth the burnout"
    ],
    "New guidelines for stroke management": [
        "window keeps expanding. we're doing thrombectomy up to 24hrs now in some cases. guidelines change faster than we can keep up",
        "every hospital does it differently. some follow guidelines strictly, others do their own thing. frustrating",
        "the 24hr window is new. we're still figuring out which patients benefit. lots of debate in our stroke group",
        "guidelines are suggestions not rules. we adapt based on patient factors. but some places are strict about it"
    ],
    "How to deal with difficult attendings": [
        "had one like that. started documenting every time they were wrong. petty but satisfying. they eventually got better",
        "just grin and bear it. not worth the fight. they'll retire eventually. or you'll graduate. either way it ends",
        "had attending who made rounds hell. talked to PD about it. nothing changed but felt good to complain",
        "started calling them out politely when they're wrong. they don't like it but at least i'm not just taking it"
    ],
    "The case that keeps me up at night": [
        "had one like that. missed subtle sign, patient had bad outcome. still think about it years later. therapy helps",
        "those cases stick with you. had one i still dream about. know it wasn't my fault but doesn't help",
        "missed something, patient died. wasn't my fault but feels like it. these cases never leave you",
        "had similar case. therapist says to practice self-compassion but easier said than done. still haunts me"
    ],
    "Board prep - UWorld vs other resources?": [
        "uworld is gold standard. expensive but worth it. also did amboss which is cheaper and pretty good",
        "did uworld and passed comfortably. know people who did other resources and passed too. uworld is just most popular",
        "uworld + first aid is the combo. expensive but you only take boards once. worth the investment",
        "did amboss instead of uworld. cheaper and passed fine. uworld is good but not the only option"
    ],
    "Rural vs urban practice - pros and cons?": [
        "rural pays more but isolation is real. did rural for 2 years then moved to city. missed having colleagues",
        "urban has better resources but more bureaucracy. rural is more autonomous but you're on your own",
        "rural: better pay, more autonomy, but isolated. urban: better support, more resources, but more red tape",
        "did rural. loved the autonomy and pay but missed city life. moved back after 3 years. depends on what you want"
    ],
    "The most satisfying diagnosis you've made": [
        "had patient with weird symptoms. did deep dive, found rare diagnosis. patient got better. felt like house for a day",
        "diagnosed something rare that everyone missed. patient was grateful. those moments make it all worth it",
        "had case where everyone was stumped. did some research, found the answer. patient recovered. best feeling",
        "diagnosed something that had been missed for months. patient finally got treatment. those wins keep you going"
    ],
    "Residency program red flags": [
        "red flags: high turnover, unhappy residents, attendings who are mean, no work-life balance",
        "if residents look miserable, run. if attendings are toxic, run. if call schedule is insane, run",
        "red flags: no meal money, terrible call schedule, mean attendings, high burnout rate",
        "if program director doesn't care about residents, that's biggest red flag. also if no one is happy there"
    ],
    "How much should I be saving as a resident?": [
        "save what you can. max out roth ira if possible. don't kill yourself trying to save everything",
        "trying to max roth ira. it's hard on resident salary but worth it. compound interest is your friend",
        "save 10-20% if you can. but also live your life. you'll make attending money soon enough",
        "saving what i can but not stressing. will catch up as attending. don't sacrifice everything now"
    ],
    "The evolution of medical education": [
        "training has changed a lot. less autonomy, more oversight. is it better? debatable. we're safer but less prepared",
        "older attendings had way more autonomy. we have more oversight. both have pros and cons",
        "training is different now. more documentation, less hands-on. are we better doctors? not sure",
        "less autonomy but more safety. more oversight but less independence. training has changed for better and worse"
    ],
    "Interesting surgical case - laparoscopic vs open": [
        "had similar debate. attending wanted open, i wanted lap. they were right. experience matters more than literature sometimes",
        "laparoscopic is newer but open is sometimes better. depends on the case. experience trumps what books say",
        "had case where literature said lap but attending did open. was right call. sometimes experience knows best",
        "learning to trust attendings' experience. they've seen things literature hasn't caught up to yet"
    ],
    "Dealing with patient families": [
        "families are the worst part sometimes. had one today who questioned everything. just smile and nod",
        "difficult families are exhausting. had one who was rude to everyone. just have to stay professional",
        "families can be challenging. had one who was demanding and rude. just have to maintain professionalism",
        "difficult families are part of the job. just have to stay calm and professional even when they're not"
    ],
    "The future of radiology": [
        "ai will change things but not replace us. more like a tool to help. the liability question is interesting",
        "ai is getting scary good. think it'll change how we practice but we'll still be needed for complex cases",
        "ai will handle routine stuff, we'll do complex cases. might actually improve our lifestyle",
        "ai is advancing fast. think it'll augment not replace. but who knows. 10 years is a long time"
    ],
    "Work-life balance in different specialties": [
        "derm and rads are lifestyle-friendly but not perfect. still work hard. other specialties are worse",
        "rads is good lifestyle but still busy. derm is great. surgery is terrible. depends on specialty",
        "lifestyle varies a lot. derm/rads are best. surgery/em are worst. everything else is in between",
        "rads is pretty good. derm is best. surgery is worst. everything else depends on practice setting"
    ]
}

def generate_comment_content(post_title, post_content, specialty=None):
    """Generate realistic, meaningful comment content specific to the post"""
    # Get post-specific comments if available
    if post_title in POST_SPECIFIC_COMMENTS:
        return random.choice(POST_SPECIFIC_COMMENTS[post_title])
    
    # Fallback: generate contextual response based on keywords
    post_lower = (post_title + " " + post_content).lower()
    
    # Try to match specific topics
    if "call" in post_lower or "shift" in post_lower:
        return random.choice([
            "our program caps at 24hrs but feels the same. post-call delirium is real",
            "q4 call here. it's brutal. by day 3 i'm basically a zombie",
            "28hrs is insane. we do q5 which is slightly better but still terrible"
        ])
    elif "salary" in post_lower or "compensation" in post_lower or "negotiate" in post_lower:
        return random.choice([
            "always negotiate. got extra 30k just by asking. worst they say is no",
            "negotiated from 320k to 360k. asked for more base and better benefits. got both",
            "don't feel greedy - it's expected. i asked for 50k more and they met me halfway"
        ])
    elif "balance" in post_lower or "life" in post_lower:
        return random.choice([
            "it's impossible tbh. try to set boundaries but they don't really exist in medicine",
            "started saying no to extra shifts. money is nice but sanity is nicer",
            "set hard boundaries with my program. no extra shifts unless emergency. they weren't happy but i'm still here"
        ])
    elif "case" in post_lower or "patient" in post_lower:
        return random.choice([
            "interesting case. had similar one last month. these stick with you",
            "good catch. always trust your gut even when workup looks normal",
            "cases like this are why medicine is interesting. thanks for sharing"
        ])
    else:
        # Generic but still meaningful
        return random.choice([
            "this is helpful. hadn't thought about it this way. thanks for the perspective",
            "interesting take. makes me reconsider my approach. appreciate you sharing",
            "good point. this is something i've been thinking about too. helpful to hear your experience"
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

def cleanup_existing_fake_content(app, users):
    """Delete all existing fake posts and comments"""
    print("\nCleaning up existing fake content...")
    
    fake_user_ids = [u.id for u in users]
    
    # Get all posts by fake users
    fake_posts = ForumPost.query.filter(ForumPost.author_id.in_(fake_user_ids)).all()
    
    if fake_posts:
        post_ids = [p.id for p in fake_posts]
        
        # Delete votes on comments
        fake_comments = ForumComment.query.filter(ForumComment.post_id.in_(post_ids)).all()
        comment_ids = [c.id for c in fake_comments]
        if comment_ids:
            ForumVote.query.filter(ForumVote.comment_id.in_(comment_ids)).delete()
        
        # Delete votes on posts
        ForumVote.query.filter(ForumVote.post_id.in_(post_ids)).delete()
        
        # Delete comments
        ForumComment.query.filter(ForumComment.post_id.in_(post_ids)).delete()
        
        # Delete posts
        ForumPost.query.filter(ForumPost.id.in_(post_ids)).delete()
        
        db.session.commit()
        print(f"✅ Deleted {len(fake_posts)} existing fake posts and their comments")
    else:
        print("✅ No existing fake posts to clean up")

def generate_forum_content(app, users):
    """Generate forum posts, comments, and votes"""
    print("\nGenerating forum posts...")
    
    # Clean up existing fake content first
    cleanup_existing_fake_content(app, users)
    
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
                    # Replies should be meaningful, not just lazy affirmations
                    # Generate based on parent comment context
                    parent_lower = comment.content.lower()
                    if "negotiate" in parent_lower or "salary" in parent_lower:
                        reply_content = random.choice([
                            "yeah i asked for more too. they gave me extra 25k. always worth asking",
                            "negotiated my offer from 340k to 380k. asked for better retirement match too",
                            "same. got extra pto and sign-on bonus just by asking. they expect it"
                        ])
                    elif "call" in parent_lower or "shift" in parent_lower:
                        reply_content = random.choice([
                            "q4 call here too. it's brutal. by day 3 i'm seeing things",
                            "our program does q5 which is slightly better but still terrible",
                            "28hrs is insane. we cap at 24 but feels the same"
                        ])
                    elif "case" in parent_lower or "patient" in parent_lower:
                        reply_content = random.choice([
                            "had similar case. those subtle signs are easy to miss",
                            "good point. always trust your gut even when workup looks normal",
                            "interesting. hadn't thought about it that way"
                        ])
                    else:
                        # Still meaningful, not just "same" or "fr"
                        reply_content = random.choice([
                            "yeah that's a good point. hadn't considered that angle",
                            "makes sense. my experience was similar but slightly different",
                            "interesting perspective. makes me think about it differently",
                            "yeah i've seen that too. adds another layer to consider"
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
            # Show which database we're using
            db_uri = app.config.get('SQLALCHEMY_DATABASE_URI', 'unknown')
            if 'sqlite' in db_uri.lower():
                print(f"📁 Using local SQLite database: {db_uri}")
            elif 'postgresql' in db_uri.lower():
                # Mask password in URI
                masked_uri = db_uri.split('@')[1] if '@' in db_uri else db_uri
                print(f"🌐 Using PostgreSQL database: ...@{masked_uri}")
            else:
                print(f"💾 Using database: {db_uri}")
            print()
            
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
            print("\n⚠️  NOTE: If you're viewing on production, make sure")
            print("   to run this script on the production server or")
            print("   with production database credentials!")
            print("=" * 60)
            
        except Exception as e:
            print(f"\n❌ ERROR: {e}")
            import traceback
            traceback.print_exc()
            db.session.rollback()
            sys.exit(1)

if __name__ == "__main__":
    main()

