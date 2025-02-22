import logging
import os
import json
import tempfile
import azure.functions as func
from process_to_graph import process_ifc_to_graph

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Processing IFC file upload request.")

    # Get query parameters for max_nodes and max_relationships, default values provided
    max_nodes = req.params.get("max_nodes", 1000000)
    max_relationships = req.params.get("max_relationships", 1000000)
    try:
        max_nodes = int(max_nodes)
        max_relationships = int(max_relationships)
    except ValueError:
        return func.HttpResponse("Invalid query parameters for max_nodes or max_relationships.", status_code=400)

    try:
        # Get file from the request body (expects multipart/form-data with field "file")
        file = req.files.get("file")
        if not file:
            return func.HttpResponse("No file provided in the request.", status_code=400)

        # Save uploaded file to a temporary location
        temp_dir = tempfile.gettempdir()
        file_path = os.path.join(temp_dir, file.filename)
        with open(file_path, "wb") as f:
            f.write(file.read())
        logging.info(f"File saved to temporary location: {file_path}")

        # Process the IFC file into a graph
        graph = process_ifc_to_graph(file_path, max_nodes=max_nodes, max_relationships=max_relationships)

        # Remove the temporary file
        os.remove(file_path)
        logging.info("Temporary file deleted after processing.")

        # Return the graph as JSON response
        return func.HttpResponse(json.dumps(graph), status_code=200, mimetype="application/json")

    except Exception as e:
        logging.error(f"Error processing IFC file: {e}")
        return func.HttpResponse(f"Error processing IFC file: {e}", status_code=500)
