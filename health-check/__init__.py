import azure.functions as func

def main(req: func.HttpRequest) -> func.HttpResponse:
    return func.HttpResponse("It's alive!", status_code=200, mimetype="application/json")
