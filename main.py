import json
from fastapi import FastAPI, Request, HTTPException, Query
from fastapi.responses import JSONResponse
import os
import shutil
from process_to_graph import process_ifc_to_graph

# Initialize the FastAPI app
app = FastAPI()

# Define upload directory and timeout
UPLOAD_DIR = "/tmp/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)
UPLOAD_TIMEOUT = 600  # 10 minutes

@app.post("/upload")
async def upload_chunk(
    request: Request,
    max_nodes: int = Query(50000, description="Maximum number of nodes to process"),
    max_relationships: int = Query(50000, description="Maximum number of relationships to process")
):
    """
    Handle chunked file uploads. Assemble chunks into a complete file and process it.
    """
    file_id = request.headers.get("file-id")
    chunk_number = int(request.headers.get("chunk-number", -1))
    total_chunks = int(request.headers.get("total-chunks", -1))

    # Validate inputs
    if not file_id or chunk_number == -1 or total_chunks == -1:
        raise HTTPException(status_code=400, detail="Missing required headers")

    # Create a directory for the file
    file_dir = os.path.join(UPLOAD_DIR, file_id)
    os.makedirs(file_dir, exist_ok=True)

    # Save the chunk
    chunk_path = os.path.join(file_dir, f"chunk{chunk_number}")
    with open(chunk_path, "wb") as f:
        async for chunk in request.stream():
            f.write(chunk)

    # Check if all chunks are received
    if len(os.listdir(file_dir)) == total_chunks:
        # Reassemble the file
        final_file_path = os.path.join(UPLOAD_DIR, f"{file_id}.ifc")
        with open(final_file_path, "wb") as final_file:
            for i in range(total_chunks):
                chunk_path = os.path.join(file_dir, f"chunk{i}")
                with open(chunk_path, "rb") as chunk_file:
                    shutil.copyfileobj(chunk_file, final_file)
                os.remove(chunk_path)  # Cleanup chunks
            os.rmdir(file_dir)  # Remove the directory

        # Process the IFC file into a graph
        try:
            graph = process_ifc_to_graph(final_file_path, max_nodes=max_nodes, max_relationships=max_relationships)
            os.remove(final_file_path)  # Clean up the IFC file

            response_size = len(json.dumps(graph))
            print(f"Size of the output response: {response_size} bytes")
            return JSONResponse(content=graph)
        except Exception as e:
            os.remove(final_file_path)
            raise HTTPException(status_code=500, detail=f"Error processing IFC file: {str(e)}")

    return {"message": f"Chunk {chunk_number} received"}
