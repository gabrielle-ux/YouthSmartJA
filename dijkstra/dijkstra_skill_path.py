# dijkstra_skill_path.py
# ============================================================
# DIJKSTRA'S ALGORITHM FOR SKILL RECOMMENDATION
#
# Based on the project document:
#   "The shortest (lowest effort) path from the Student node
#    (python) to the Target Job node (python, SQL, excel)
#    where SQL would give a higher score than excel, and
#    therefore recommended more heavily."
#
# GRAPH MODEL:
#   Node  = a skill STATE (the set of skills the student has)
#           e.g. frozenset({"python"})
#                frozenset({"python", "sql"})
#                frozenset({"python", "sql", "excel"})  <- target
#
#   Edge  = learning ONE new skill to move to the next state
#           e.g. {"python"} --[learn sql]--> {"python", "sql"}
#
#   Weight = 1 - cosine similarity improvement
#            lower weight = bigger score jump = Dijkstra picks it first
#
# FLOW:
#   Student node (current skills)
#       |  [learn sql]         weight = small (big improvement)
#       v
#   {"python", "sql"}
#       |  [learn excel]       weight = larger (smaller improvement)
#       v
#   {"python", "sql", "excel"} <- Target Job node
# ============================================================

import heapq
import math


# ============================================================
# COSINE SIMILARITY
# Measures how close the student's skills are to the job's skills.
# Called repeatedly to calculate the improvement each skill gives.
# ============================================================

def cosine_similarity(student_skills, job_skills):
    vocab = list(set(student_skills + job_skills))
    vec1  = [1 if s in student_skills else 0 for s in vocab]
    vec2  = [1 if s in job_skills else 0 for s in vocab]

    dot  = sum(a * b for a, b in zip(vec1, vec2))
    mag1 = math.sqrt(sum(a ** 2 for a in vec1))
    mag2 = math.sqrt(sum(b ** 2 for b in vec2))

    if mag1 == 0 or mag2 == 0:
        return 0.0
    return dot / (mag1 * mag2)


# ============================================================
# DIJKSTRA'S ALGORITHM
#
# INPUT:
#   student_skills : list of skills the student currently has
#                    e.g. ["python"]
#   job_skills     : list of skills the job requires
#                    e.g. ["python", "sql", "excel"]
#
# OUTPUT:
#   list of steps from student node to target job node:
#   [
#     { "learn": "sql",   "state": ["python", "sql"],          "score": 72 },
#     { "learn": "excel", "state": ["python", "sql", "excel"], "score": 100 },
#   ]
# ============================================================

def dijkstra_skill_path(student_skills, job_skills):
    # Normalize to lowercase
    student_skills = [s.lower().strip() for s in student_skills]
    job_skills     = [s.lower().strip() for s in job_skills]

    # Find what's missing
    missing_skills = [s for s in job_skills if s not in student_skills]

    if not missing_skills:
        return []  # Already at the target node!

    # --- Setup ---
    # Nodes are frozensets (hashable sets) representing skill states
    start_node  = frozenset(student_skills)
    target_node = frozenset(job_skills)

    # dist[node] = lowest total cost to reach this skill state
    dist = {start_node: 0.0}

    # prev[node] = (previous_node, skill_learned) to reconstruct path later
    prev = {start_node: None}

    # Priority queue: (cost, tiebreaker, node)
    # frozensets aren't comparable so we use a counter as tiebreaker
    counter = 0
    pq      = [(0.0, counter, start_node)]
    visited = set()

    while pq:
        current_cost, _, current_node = heapq.heappop(pq)

        if current_node in visited:
            continue
        visited.add(current_node)

        if current_node == target_node:
            break

        # --- Explore edges ---
        # Each edge = learning one skill not yet in current state
        current_skills       = list(current_node)
        skills_still_missing = [s for s in job_skills if s not in current_node]

        for skill in skills_still_missing:
            # Next state = current skills + this new skill
            next_node   = current_node | frozenset([skill])
            next_skills = list(next_node)

            # How much does learning this skill improve the cosine similarity?
            score_before = cosine_similarity(current_skills, job_skills)
            score_after  = cosine_similarity(next_skills, job_skills)
            improvement  = score_after - score_before

            # Edge weight = 1 - improvement
            # Big improvement = low weight = Dijkstra picks this path first
            edge_weight = 1 - improvement if improvement > 0 else 1.0
            new_cost    = current_cost + edge_weight

            if next_node not in dist or new_cost < dist[next_node]:
                dist[next_node] = new_cost
                prev[next_node] = (current_node, skill)
                counter += 1
                heapq.heappush(pq, (new_cost, counter, next_node))

    # --- Reconstruct the path from start node to target node ---
    path = []
    node = target_node

    # If target was never reached return empty
    if node not in prev:
        return []

    while prev[node] is not None:
        previous_node, skill_learned = prev[node]
        score = round(cosine_similarity(list(node), job_skills) * 100)
        path.append({
            "learn": skill_learned,         # skill to learn at this step
            "state": sorted(list(node)),    # full skill set after learning it
            "score": score,                 # match % after this step
        })
        node = previous_node

    # Path was built backwards so reverse it
    path.reverse()
    return path


# ============================================================
# EXAMPLE RUN
# ============================================================

if __name__ == "__main__":
    student_skills = ["python"]
    job_skills     = ["python", "sql", "excel", "tableau"]

    print("Student node :", student_skills)
    print("Target node  :", job_skills)

    start_score = round(cosine_similarity(student_skills, job_skills) * 100)
    print(f"\nStarting score: {start_score}%")
    print("\nDijkstra's shortest path to target job:\n")

    path = dijkstra_skill_path(student_skills, job_skills)

    for i, step in enumerate(path, 1):
        print(f"  Step {i}: Learn '{step['learn'].upper()}'")
        print(f"          State -> {step['state']}")
        print(f"          Score -> {step['score']}%\n")

    if path:
        print(f"Final score: {path[-1]['score']}%")
