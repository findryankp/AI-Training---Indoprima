from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai_tools import RagTool, PDFSearchTool, FileReadTool

@CrewBase
class CrewRag():
    """CrewRag crew"""

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    # Inisialisasi Tool
    fileRead = FileReadTool()

    @agent
    def doc_analyzer(self) -> Agent:
        return Agent(
            config=self.agents_config['doc_analyzer'], # type: ignore[index]
            verbose=True,
            tools=[self.fileRead]
        )

    @agent
    def doc_resumer(self) -> Agent:
        return Agent(
            config=self.agents_config['doc_resumer'], # type: ignore[index]
            verbose=True,
        )

    @task
    def documen_analyzer_task(self) -> Task:
        return Task(
            config=self.tasks_config['documen_analyzer_task'], # type: ignore[index]
        )

    @task
    def doc_resumer_task(self) -> Task:
        return Task(
            config=self.tasks_config['doc_resumer_task'], # type: ignore[index]
        )

    @crew
    def crew(self) -> Crew:
        """Membuat instance Crew dengan proses sekuensial"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
