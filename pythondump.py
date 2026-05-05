from collections import Counter
# This Python snippet takes your job matches and calculates which skills 
# the user should prioritize to improve their score across their entire feed.
def get_multi_job_optimization(user_skills, top_jobs):
    """
    Identifies skills that appear most frequently across multiple job gaps.
    
    :param user_skills: Set of strings (e.g., {'Python', 'SQL'})
    :param top_jobs: List of dicts containing 'job_id' and 'required_skills'
    :return: List of tuples (skill, frequency) sorted by impact
    """
    all_gaps = []
    
    for job in top_jobs:
        job_skills = set(job['required_skills'])
        # Find skills the user is missing for THIS specific job
        gap = job_skills - user_skills
        all_gaps.extend(list(gap))
    
    # Count how many times each missing skill appears across all top jobs
    skill_counts = Counter(all_gaps)
    
    # Sort skills by frequency (descending)
    optimized_recommendations = skill_counts.most_common()
    
    return optimized_recommendations

# Example Usage:
user_resume_skills = {'Python', 'Flask', 'HTML'}
matched_jobs = [
    {'id': 101, 'required_skills': ['Python', 'SQL', 'AWS']},
    {'id': 102, 'required_skills': ['Python', 'Docker', 'SQL']},
    {'id': 103, 'required_skills': ['Flask', 'SQL', 'NoSQL']}
]

recommendations = get_multi_job_optimization(user_resume_skills, matched_jobs)
# Result: [('SQL', 3), ('AWS', 1), ('Docker', 1), ('NoSQL', 1)]




# The n8n workflow acts as the bridge between your Flask app and the Kaggle API.A. 
# Flask-Side TriggerIn your Flask route, you will use the requests library to send the 
# prioritized missing skills to your n8n Webhook node.
import requests

def trigger_n8n_search(missing_skills):
    # Your n8n Production Webhook URL
    webhook_url = "https://your-n8n-instance.com"
    
    payload = {
        "skills": missing_skills,  # e.g., ["SQL", "Docker"]
        "user_id": 123
    }
    
    response = requests.post(webhook_url, json=payload)
    return response.json()


# bookmarks logic
@app.route('/bookmark/<int:job_id>', methods=['POST'])
@login_required
def bookmark_job(job_id):
    # Re-calculate or pull current scores from the feed session
    current_match = calculate_cosine_score(user_id, job_id)
    current_pref = calculate_preference_score(user_id, job_id)
    
    new_bookmark = Bookmark(
        user_id=current_user.id,
        job_id=job_id,
        saved_match_score=current_match,
        saved_pref_score=current_pref
    )
    db.session.add(new_bookmark)
    db.session.commit()
    return {"message": "Job saved with current scores!"}
