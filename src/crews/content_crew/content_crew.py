from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task

@CrewBase
class ContentCrew:
    """Content Crew untuk pembuatan konten blog"""

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    @agent
    def planner(self) -> Agent:
        return Agent(config=self.agents_config["planner"])

    @agent
    def writer(self) -> Agent:
        return Agent(config=self.agents_config["writer"])

    @agent
    def editor(self) -> Agent:
        return Agent(config=self.agents_config["editor"])

    @task
    def planning_task(self) -> Task:
        return Task(config=self.tasks_config["planning_task"])

    @task
    def writing_task(self) -> Task:
        return Task(config=self.tasks_config["writing_task"])

    @task
    def editing_task(self) -> Task:
        return Task(config=self.tasks_config["editing_task"])

    @crew
    def crew(self) -> Crew:
        """Membuat instance Crew dengan proses sekuensial"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
