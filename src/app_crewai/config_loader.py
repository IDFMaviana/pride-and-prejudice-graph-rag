from pathlib import Path
from typing import Dict
from utils.config import settings

OPENAI_API_KEY = settings.OPENAI_API_KEY
OPENAI_MODEL = settings.OPENAI_MODEL

import yaml
from crewai import Agent,Task

def _load_yaml(path:str |Path) -> dict:
    path = Path(path)
    with path.open("r", encoding = "utf-8") as f:
        return yaml.safe_load(f) or {}

def load_agents(path: str | Path) -> Dict[str, Agent]:
    data = _load_yaml(path)
    agents: Dict[str, Agent] = {}

    for name, cfg in data.items():
        agents[name] = Agent(
            role=cfg["role"],
            goal=cfg["goal"],
            backstory=cfg.get("backstory", ""),
            verbose=cfg.get("verbose", True),
            allow_delegation=cfg.get("allow_delegation", False),
            llm=OPENAI_MODEL,
        )
    return agents

def load_tasks(path: str |Path) -> Dict[str, Task]:
    data = _load_yaml(path)
    tasks_section = data.get("tasks", data)

    tasks: Dict[str, Task] = {}
    for name, cfg in tasks_section.items():
        tasks[name] = Task(
            description=cfg["description"],
            expected_output=cfg.get("expected_output", ""),
            async_execution=cfg.get("async_execution", False),
        )
    return tasks