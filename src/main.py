from utils.config import settings
import os
from app_crewai.crew import PrideAndPrejudiceCrew



OPENAI_API_KEY = settings.OPENAI_API_KEY
OPENAI_MODEL = settings.OPENAI_MODEL


def run_crew_interactive():
    crew = PrideAndPrejudiceCrew()

    question = "what`s the difference of Mr.Ellizabeth from the chapter 1 to the chapter 5?"
    result = crew.run(question)

    print("\n===== Crew =====")
    print(result)

if __name__ == "__main__":
    run_crew_interactive()