import os
from pathlib import Path
from typing import Dict

import yaml
from crewai import Crew, Process
from crewai_tools import MCPServerAdapter
from mcp import StdioServerParameters
from utils.config import paths


from .config_loader import load_agents, load_tasks


SRC_DIR = paths.CREW_DIR
AGENTS_PATH = paths.AGENT_DIR
TASKS_PATH = paths.TASKS_DIR

def _load_task_agent_mapping(path: Path) -> Dict[str, str]:
    """Return an ordered mapping task_name -> agent_name from the YAML config."""
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    tasks_section = data.get("tasks", data)
    mapping: Dict[str, str] = {}

    for task_name, cfg in tasks_section.items():
        agent_name = cfg.get("agent")
        if agent_name:
            mapping[task_name] = agent_name

    return mapping


class PrideAndPrejudiceCrew:
    """Wire agents and tasks from configuration and run the crew."""

    def __init__(self) -> None:
        self.agents = load_agents(AGENTS_PATH)
        self.tasks = load_tasks(TASKS_PATH)
        self.task_agent_mapping = _load_task_agent_mapping(TASKS_PATH)

    def run(self, user_question: str) -> str:
        server_params = StdioServerParameters(
            command="python",
            args=["-u", "-m", "app_crewai.tools.mcp_server"],
            env=os.environ.copy(),
            cwd=str(SRC_DIR),
        )

        with MCPServerAdapter(server_params) as tools:
            tool_list = list(tools)

            graph_tools = [t for t in tool_list if t.name == "run_cypher"]
            semantic_tools = [t for t in tool_list if t.name == "semantic_pinecone_search"]

            # Attach tools based on which tasks an agent owns
            for task_name, agent_name in self.task_agent_mapping.items():
                agent = self.agents.get(agent_name)
                if agent is None:
                    continue

                if task_name == "graph_relationship_extraction":
                    agent.tools = graph_tools
                elif task_name == "semantic_scene_retrieval":
                    agent.tools = semantic_tools

            # Associate each task with its configured agent
            for task_name, agent_name in self.task_agent_mapping.items():
                task = self.tasks.get(task_name)
                agent = self.agents.get(agent_name)

                if task is not None and agent is not None:
                    task.agent = agent

            # Preserve task order as defined in the YAML mapping
            crew_tasks = [
                self.tasks[name]
                for name in self.task_agent_mapping.keys()
                if name in self.tasks
            ]

            used_agents = {
                agent_name for agent_name in self.task_agent_mapping.values()
                if agent_name in self.agents
            }
            crew_agents = [self.agents[name] for name in used_agents]

            crew = Crew(
                agents=crew_agents,
                tasks=crew_tasks,
                process=Process.sequential,
                verbose=True,
            )

            result = crew.kickoff(inputs={"user_question": user_question})
            return str(result)
