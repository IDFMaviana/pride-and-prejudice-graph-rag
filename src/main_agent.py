import os
from crewai import Agent, Task, Crew, Process
from langchain_google_genai import ChatGoogleGenerativeAI
from utils.config import settings


# Configurar o LLM que os agentes irão usar
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key=settings.GOOGLE_API_KEY
)

class PrideAgent:
    # Agente 1: Relationship specialist
    def graph_agent(self) -> Agent:
        return Agent(
        role='Graph Database Specialist',
        goal='Analyze and extract information about the relationships between characters from the Neo4j database.',
        backstory='You are an expert in Neo4j and the Cypher query language. Your role is to receive questions about relationships and translate them into Cypher queries to extract accurate structured data from the graph.',
        verbose=True,
        allow_delegation=False,
        llm=llm,
        # tools=[neo4j_tool]
        )
    
    def semantic_agent(self) -> Agent:
        return Agent(
            role='Semantic Search Specialist',
            goal='Find and retrieve the most relevant scene summaries from the Pinecone vector database.',
            backstory='You are a specialist in similarity search. Your role is to receive questions about events or descriptions and find the most contextually relevant text passages in the vector database.',
            verbose=True,
            allow_delegation=False,
            llm=llm,
            # tools=[pinecone_tool] 
    )
    def literary_agent(self) -> Agent:
        return Agent(
            role='Literary Analyst and Project Manager',
            goal='Provide complete and insightful answers about the novel "Pride and Prejudice" using data from the specialists.',
            backstory='You are a renowned expert on the works of Jane Austen. Your role is to receive a user question, coordinate the data gathering from the database specialists, and then synthesize that information into a cohesive, well-written, and easy-to-understand response.',
            verbose=True,
            allow_delegation=True, # This agent can delegate tasks
            llm=llm
)