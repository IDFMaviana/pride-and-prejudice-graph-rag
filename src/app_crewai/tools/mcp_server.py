import os
from typing import Any, Dict, List, Optional

from mcp.server.fastmcp import FastMCP
from neo4j import GraphDatabase
from pydantic import BaseModel
from utils.config import settings
from pinecone import Pinecone, ServerlessSpec
from langchain_google_genai import GoogleGenerativeAIEmbeddings


URI = settings.NEO4J_URI
USER = settings.NEO4J_USER
PASSWORD = settings.NEO4J_PASSWORD
PINECONE_API_KEY = settings.PINECONE_API_KEY
PINECONE_INDEX_NAME = settings.PINECONE_INDEX_NAME
GOOGLE_API_KEY = settings.GOOGLE_API_KEY

mcp = FastMCP("Neo4j-pride-graph")
driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))

pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index(PINECONE_INDEX_NAME)

# Embedding model
embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001", google_api_key=settings.GOOGLE_API_KEY)

class CypherRequest(BaseModel):
    query: str
    params: Optional[Dict[str,Any]] = None

class CharacterRelationsRequest(BaseModel):
    name: str
    limit: int = 20

class SemanticSearchRequest(BaseModel):
    query: str
    top_k: int = 5

@mcp.tool()
def run_cypher(body:CypherRequest) -> List[Dict[str,Any]]:
    """
    Executes a cypher query to read graph nodes and relationship
    """
    with driver.session() as session:
        result = session.run(body.query, **(body.params or {}))
        return [record.data() for record in result]

@mcp.tool()
def semantic_pinecone_search(body:SemanticSearchRequest) -> List[Dict[str,Any]]:
    """
    Performs semantic search over the Pinecone index populated
    with Pride and Prejudice scene summaries.
    """
    query_vector = embeddings.embed_query(body.query)
    res = index.query(
        vector=query_vector,
        top_k=body.top_k,
        include_metadata=True,
    )
    matches = res.get("matches", [])
    return [
        {
            "id": m["id"],
            "score": m["score"],
            "metadata": m.get("metadata", {}),
        }
        for m in matches
    ]

if __name__ == "__main__":
   mcp.run(transport='stdio')