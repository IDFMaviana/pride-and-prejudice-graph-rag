from utils.config import settings,paths
from pinecone import Pinecone,ServerlessSpec
from langchain_google_genai import GoogleGenerativeAIEmbeddings
import json
import time

#Functions
def load_all_extractions(filepath, is_json):
    #load extractions from the book
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f) if is_json else f.read()
    except FileNotFoundError:
        print(f"Error: file not found. Path: {filepath}")
        return None
    except json.JSONDecodeError:
        print(f"Error: JSON decode: {filepath}")
        return None

def prepare_documents_for_embedding(all_chapters):
    #Converts chapter data into LangChain's Document format using 'interaction_summary' as content and everything else as metadata.
    documents = []
    for i, chapter_data in enumerate(all_chapters):
        scene = chapter_data.get("data", {})
        text_to_embbed = scene.get("interaction_summary", "No summary available.")
        
        metadata = {
            "chapter_id": scene.get("chapter_id"), 
            "setting": scene.get("setting"),
            "themes": ", ".join(scene.get("themes", [])),
            "characters": ", ".join([c.get("character_name") for c in scene.get("characters", []) if c.get("character_name")]),
            "emotional_tone": scene.get("emotional_tone"),
            "power_dynamics": scene.get("power_dynamics"),
            "plot_development": scene.get("plot_development"), 
            "relationship_development": scene.get("relationship_development"),
            "authorial_style": scene.get("authorial_style"), 
            "historical_context": scene.get("historical_context"),
            "irony": scene.get("irony"),
            "dialogue_highlights": "\n---\n".join(scene.get("dialogue_highlights", []))
        }
        
        metadata = {k: str(v) for k, v in metadata.items() if v is not None}
        unique_id = scene.get('chapter_id', i+1)

        documents.append({"id":unique_id,"text":text_to_embbed,"metadata":metadata})
    
    return documents

def main():
    print(settings.PINECONE_INDEX_NAME)
    pc = Pinecone(api_key=settings.PINECONE_API_KEY)
    print("Pinecone connection established",sep="\n")
    #verify if the index exists
    if settings.PINECONE_INDEX_NAME not in pc.list_indexes().names():
        pc.create_index(
            name=settings.PINECONE_INDEX_NAME,
            dimension=3072,
            metric='cosine',
            spec=ServerlessSpec(
                cloud='aws',
                region='us-east-1'
            )
        )
        print(f"Index {settings.PINECONE_INDEX_NAME} created.",sep="\n")
    else:
        print(f"Index found... loading...",sep="\n")

    #Load the index
    index = pc.Index(settings.PINECONE_INDEX_NAME)
    #Load the extracted document
    document = load_all_extractions(paths.PROCESSED_F_DIR,True)
    #Prepare the document for pinecone
    documents = prepare_documents_for_embedding(document)

    # Embedding model
    embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001", google_api_key=settings.GOOGLE_API_KEY)
    batch_size = 50 
    print(f"Starting to create embeddings and upsert to Pinecone in batches of {batch_size}...")
    
    for i in range(0, len(documents), batch_size):
        batch = documents[i:i + batch_size]
        batch_texts = [doc['text'] for doc in batch]
        
        print(f"  - Processing batch {i//batch_size + 1}...")
        
        # Create embeddings for the batch of texts
        batch_embeddings = embeddings.embed_documents(batch_texts)
        
        # Prepare the data for upsert in the format Pinecone expects
        vectors_to_upsert = []
        for j, doc in enumerate(batch):
            vectors_to_upsert.append({
                "id": doc['id'],
                "values": batch_embeddings[j],
                "metadata": doc['metadata']
            })
        
        # Upsert the batch to Pinecone
        index.upsert(vectors=vectors_to_upsert)
        print(f"  - Batch {i//batch_size + 1} successfully upserted.")
        time.sleep(1)

    print(f"\nLoading complete!")
    print(f"{len(documents)} vectors were upserted to index '{settings.PINECONE_INDEX_NAME}'.")


#main()