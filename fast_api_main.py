import json
import tempfile
from fastapi import FastAPI, Request, HTTPException, Query, UploadFile, File
from fastapi.responses import JSONResponse
import os
import shutil
from process_to_graph import process_ifc_to_graph
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"]
)

# Define upload directory and timeout
UPLOAD_DIR = os.path.join(tempfile.gettempdir(), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)
print(f"Upload directory: {UPLOAD_DIR}")
os.makedirs(UPLOAD_DIR, exist_ok=True)
UPLOAD_TIMEOUT = 600  # 10 minutes

@app.post("/api/upload")
async def upload_complete_file(
    file: UploadFile = File(...),
    max_nodes: int = Query(1000000, description="Maximum number of nodes to process"),
    max_relationships: int = Query(1000000, description="Maximum number of relationships to process")
):
    """
    Handle complete IFC file uploads and process them.
    """
    try:
        file_path = os.path.join(UPLOAD_DIR, file.filename)
        with open(file_path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        # Process the IFC file into a graph
        graph = process_ifc_to_graph(file_path, max_nodes=max_nodes, max_relationships=max_relationships)
        os.remove(file_path)  # Clean up file after processing
        return JSONResponse(content=graph)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing IFC file: {str(e)}")


@app.post("/api/upload-chunk")
async def upload_chunk(
    request: Request,
    max_nodes: int = Query(1000000, description="Maximum number of nodes to process"),
    max_relationships: int = Query(1000000, description="Maximum number of relationships to process")
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

    # Log chunk details
    chunk_size = os.path.getsize(chunk_path)
    print(f"Chunk {chunk_number} saved at {chunk_path} ({chunk_size} bytes)")

    # Check if all chunks are received
    if len(os.listdir(file_dir)) == total_chunks:
        # Reassemble the file
        final_file_path = os.path.join(UPLOAD_DIR, f"{file_id}.ifc")
        print(f"All chunks received. Reassembling file: {final_file_path}")
        with open(final_file_path, "wb") as final_file:
            for i in range(total_chunks):
                chunk_path = os.path.join(file_dir, f"chunk{i}")
                chunk_size = os.path.getsize(chunk_path)
                print(f"Adding chunk {i} ({chunk_size} bytes) from {chunk_path} to {final_file_path}")
                with open(chunk_path, "rb") as chunk_file:
                    shutil.copyfileobj(chunk_file, final_file)
                os.remove(chunk_path)  # Cleanup chunks
                print(f"Chunk {i} deleted: {chunk_path}")

        # Remove the directory after all chunks are reassembled
        os.rmdir(file_dir)
        final_file_size = os.path.getsize(final_file_path)
        print(f"File reassembled successfully: {final_file_path} ({final_file_size} bytes)")

        # Process the IFC file into a graph
        try:
            graph = process_ifc_to_graph(final_file_path, max_nodes=max_nodes, max_relationships=max_relationships)
            os.remove(final_file_path)  # Clean up the IFC file
            print(f"Reassembled file processed and deleted: {final_file_path}")

            response_size = len(json.dumps(graph))
            print(f"Size of the output response: {response_size} bytes")
            return JSONResponse(content=graph)
        except Exception as e:
            print(f"Error processing IFC file: {e}")
            os.remove(final_file_path)
            raise HTTPException(status_code=500, detail=f"Error processing IFC file: {str(e)}")

    return {"message": f"Chunk {chunk_number} received"}

