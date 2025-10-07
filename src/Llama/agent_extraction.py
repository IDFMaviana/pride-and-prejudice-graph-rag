from llama_cloud_services import LlamaExtract
from llama_cloud_services.extract.extract import StatusEnum
from llama_cloud import ExtractConfig, ExtractMode, ChunkMode, ExtractTarget
import json
import os
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).resolve().parent.parent))
from utils.config import paths, settings
import asyncio
import re
import time


# Function to load files
def load_files(filepath, is_json):
    """Load files"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f) if is_json else f.read()
    except FileNotFoundError:
        print(f"Error: file not found. Path: {filepath}")
        return None
    except json.JSONDecodeError:
        print(f"Error: JSON decode: {filepath}")
        return None
    
def list_chapters(path):
    #Sort and list files
    chapter_files = sorted(
        [f for f in os.listdir(path) if f.endswith('.txt')],
        key=lambda x: int(re.search(r'(\d+)', x).group()) if re.search(r'(\d+)', x) else 0
    )
    if not chapter_files:
        raise FileNotFoundError(f"There's no files in: {path}")
    # Retorna apenas os caminhos completos
    return [os.path.join(path, f) for f in chapter_files]

# Define the system prompt
system_prompts = load_files(paths.SYSTEM_PROMPT_DIR,False) 

# Define the extraction schema
schema = load_files(paths.EXTRACTION_SCHEMA_DIR,True)
#The agent name
my_agent = "extraction agent"

#Define the destination dir
processed_dir = paths.PROCESSED_DIR / "processed_book.json"

extractor = LlamaExtract(api_key = settings.LLAMA_API_KEY)

# Get or create the agent
try:
    print("getting the extracting agent...", sep="\n")
    agent = extractor.get_agent(name=my_agent)
except:
    print("Creating the agent...", sep="\n")
    #Extraction agent config
    config = ExtractConfig(
    extraction_mode = ExtractMode.BALANCED,
    extraction_target= ExtractTarget.PER_DOC,
    system_prompt=system_prompts,
    chunk_mode=ChunkMode.SECTION)

    agent = extractor.create_agent(name=my_agent,
                                   data_schema=schema,
                                   config=config)

# list of chapters
chapter_files = list_chapters(paths.PRE_PROCESSED_DIR)
# Wait until all jobs finish
async def wait_for_jobs(agent, jobs, interval=5):

    pending = {job.id for job in jobs}
    start_time = time.time()

    while pending:
        print(f"Waiting for {len(pending)} documents...", sep="\n")
        done = set()

        for job_id in pending:
            job = agent.get_extraction_job(job_id)
            if job.status in [StatusEnum.SUCCESS, StatusEnum.ERROR]:
                print(f"Job {job_id} done: {job.status}")
                done.add(job_id)

        pending -= done
        if pending:
            await asyncio.sleep(interval)

        # security timeout
        if time.time() - start_time > 1800:  # 30 minutes
            raise TimeoutError("Timeout")

    print("All jobs done")

async def main():
    batch_size = 10 
    all_final_data = []

    for i in range(0, len(chapter_files), batch_size):
        batch_files = chapter_files[i:i + batch_size]
        batch_number = (i // batch_size) + 1
        print(f"--- Processing Batch {batch_number} ---",sep = "\n")

        # Queue extraction files for the current batch
        jobs = await agent.queue_extraction(batch_files)
        print(f"{len(jobs)} jobs sent to extraction for this batch")
        
        await wait_for_jobs(agent, jobs)

        results = [agent.get_extraction_run_for_job(job.id) for job in jobs]
        #Get the result of extraction and save
        batch_data = []
        for result in results:
            if result and hasattr(result, 'data') and result.data:
                chapter_id = result.data.get("chapter_id", f"unknown_chapter_batch_{batch_number}") 
                batch_data.append({
                    "Chapter": chapter_id,
                    "data": result.data
                })
            else:
                print(f"Warning: Received an empty or invalid result for a job in batch {batch_number}")

        # If there's new data, read the existing file, append, and write it back
        if batch_data:
            existing_data = []
            try:
                # Try to read the existing data from the file
                with open(processed_dir, "r", encoding="utf-8") as f:
                    existing_data = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                # If the file doesnt exist or is empty/invalid, start with an empty list
                print("Output file not found or empty. Creating a new one.")
                existing_data = []

            # Append the new batch data to the existing data
            existing_data.extend(batch_data)

            # Write the entire updated list back to the file
            with open(processed_dir, "w", encoding="utf-8") as f:
                json.dump(existing_data, f, ensure_ascii=False, indent=4)
            
            print(f"Successfully saved {len(batch_data)} results from Batch {batch_number}. Total results in file: {len(existing_data)}")
        
        print(f"--- Batch {batch_number} finished. Pausing for 5 seconds... ---")
        await asyncio.sleep(5)
    print("Finish: All batches processed and data saved.",sep = "\n")

asyncio.run(main())