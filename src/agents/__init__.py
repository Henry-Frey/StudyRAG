"""Agent registry for StudyRAG."""
from src.agents.explainer_agent import ExplainerAgent
from src.agents.quiz_agent import QuizAgent
from src.agents.connector_agent import ConnectorAgent
from src.agents.summarizer_agent import SummarizerAgent

AGENT_REGISTRY = {
    "explainer": ExplainerAgent,
    "quiz": QuizAgent,
    "connector": ConnectorAgent,
    "summarizer": SummarizerAgent,
}

__all__ = ["AGENT_REGISTRY", "ExplainerAgent", "QuizAgent", "ConnectorAgent", "SummarizerAgent"]
