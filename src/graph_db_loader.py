import os
import json
import re
from neo4j import GraphDatabase
from utils.config import paths, settings

class Neo4jLoader:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri,auth=(user,password))
        print("Neo4j connection established")
    #Close the connection
    def close(self):
        self.driver.close()
        print("Neo4j connection closed")
    
    def _execute_query(self, tx, query, parameters={}):
        
        print(f"Executing query: {query}")
        print(f"With parameters: {json.dumps(parameters, indent=2)}")
        tx.run(query, parameters)
    
    def create_constraints(self):
        #create a constraint to ensure unique characters
        query = "CREATE CONSTRAINT IF NOT EXISTS FOR (c:Character) REQUIRE c.name IS UNIQUE"
        with self.driver.session() as session:
            # Passamos a query sem parâmetros
            session.execute_write(self._execute_query, query)
    
    def load_character(self, character_info, chapter_id):
    
        query = """
        MERGE (c:Character {name: $name})
        ON CREATE SET
            c.description = $description,
            c.roles = [$role_in_chapter]
        ON MATCH SET
            c.description = coalesce($description, c.description),
            c.roles = CASE WHEN NOT $role_in_chapter IN c.roles THEN c.roles + $role_in_chapter ELSE c.roles END
        """
        parameters = {
            "name": character_info.get("character_name"),
            "description": character_info.get("description", "No description available."),
            # We store the role with context from the chapter
            "role_in_chapter": f"{character_info.get('role', 'Unknown role')} (in {chapter_id})"
        }
        with self.driver.session() as session:
            session.execute_write(self._execute_query, query, parameters)

    def load_interaction(self, pairwise_rel, scene_info):
        
        query = """
        MERGE (char_a:Character {name: $char_a_name})
        MERGE (char_b:Character {name: $char_b_name})
        CREATE (char_a)-[r:INTERACTS_IN {
            chapter: $chapter, setting: $setting, interaction_type: $interaction_type,
            sentiment_A_to_B: $sentiment_a_b, sentiment_B_to_A: $sentiment_b_a,
            summary: $summary, emotional_tone: $emotional_tone, power_dynamics: $power_dynamics,
            themes: $themes, plot_development: $plot_development
        }]->(char_b)
        """
        parameters = {
            "char_a_name": pairwise_rel.get("character_name_a"),
            "char_b_name": pairwise_rel.get("character_name_b"),
            "chapter": scene_info.get("chapter_id", "Unknown Chapter"),
            "setting": scene_info.get("setting", "Unknown Setting"),
            "interaction_type": pairwise_rel.get("interaction_type", "Unknown Interaction"),
            "sentiment_a_b": pairwise_rel.get("sentiment_A_to_B", "Unknown"),
            "sentiment_b_a": pairwise_rel.get("sentiment_B_to_A", "Unknown"),
            "summary": pairwise_rel.get("summary", "No summary provided."),
            "emotional_tone": scene_info.get("emotional_tone", "N/A"),
            "power_dynamics": scene_info.get("power_dynamics", "N/A"),
            "themes": scene_info.get("themes", []),
            "plot_development": scene_info.get("plot_development", "N/A")
        }
        with self.driver.session() as session:
            session.execute_write(self._execute_query, query, parameters)

def load_all_extractions(filepath, is_json):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f) if is_json else f.read()
    except FileNotFoundError:
        print(f"Error: file not found. Path: {filepath}")
        return None
    except json.JSONDecodeError:
        print(f"Error: JSON decode: {filepath}")
        return None

def main():
    #Credentials
    URI = settings.NEO4J_URI
    USER = settings.NEO4J_USER
    PASSWORD =  settings.NEO4J_PASSWORD

    loader = Neo4jLoader(URI, USER, PASSWORD)
    loader.create_constraints()

    #chapters = load_all_extractions(paths.PROCESSED_F_DIR, True)
    chapters = load_all_extractions(paths.PROCESSED_F_DIR, True)
    
    character_count = 0
    interaction_count = 0
    print("Loading characters and interactions to neo4j")

    for chapter_data in chapters:
        scene = chapter_data.get("data", {})
        chapter_id = scene.get("chapter_id", "Unknown Chapter")

        # 1. First, process the characters list
        if "characters" in scene and scene["characters"]:
            for char_info in scene["characters"]:
                if char_info.get("character_name"):
                    loader.load_character(char_info, chapter_id)
                    character_count += 1
        
        # 2. Process the interactions
        if "pairwise_relationships" in scene and scene["pairwise_relationships"]:
            for rel in scene["pairwise_relationships"]:
                char_a = rel.get("character_name_a")
                char_b = rel.get("character_name_b")

                if char_a and char_b:
                    #only load if char a and b were found
                    loader.load_interaction(rel, scene)
                    interaction_count += 1
    
    print(f"Loading complete!")
    print(f"{character_count} character appearances processed (nodes created/updated).")
    print(f"{interaction_count} interactions were added to the graph.")
    
    loader.close()

if __name__ == "__main__":
    main()