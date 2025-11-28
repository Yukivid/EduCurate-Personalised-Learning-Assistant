from fastapi import APIRouter, HTTPException
from RoadmapGeneration.agents.topic_decomposer import topic_decomposer
from RoadmapGeneration.agents.prerequisite_inference import prerequisite_inference
from RoadmapGeneration.agents.difficulty_estimator import difficulty_estimator
from RoadmapGeneration.agents.validator_agent import validator_agent
from RoadmapGeneration.agents.personalizer_agent import personalizer_agent

router = APIRouter()

@router.post("/generate-roadmap/")
def generate_roadmap(payload: dict):
    # 1. Decompose user input into knowledge nodes
    nodes = topic_decomposer(payload['query'])
    # 2. Infer prerequisites and build dependency graph
    G = prerequisite_inference(nodes)
    # 3. Estimate difficulty and time for each node
    G = difficulty_estimator(G)
    # 4. Validate structure and pedagogy
    G, issues = validator_agent(G, payload.get('original_keywords', []))
    # 5. Personalize to learner needs and create a schedule
    schedule = personalizer_agent(G, payload.get('user_model', {}), payload.get('time_budget', 0))
    return {"schedule": schedule, "issues": issues}
