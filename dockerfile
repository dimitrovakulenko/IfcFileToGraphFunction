FROM mcr.microsoft.com/azure-functions/python:4-python3.12

USER root
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y unzip curl && apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /home/site/wwwroot

ARG IFC_OPENSHELL_BUILD="39-v0.8.0-2a5e42e"
RUN curl -O https://s3.amazonaws.com/ifcopenshell-builds/ifcopenshell-python-${IFC_OPENSHELL_BUILD}-linux64.zip && \
    unzip ifcopenshell-python-${IFC_OPENSHELL_BUILD}-linux64.zip && \
    rm ifcopenshell-python-${IFC_OPENSHELL_BUILD}-linux64.zip

COPY requirements.txt .
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONPATH="/home/site/wwwroot/ifcopenshell:${PYTHONPATH}" \
    AzureWebJobsScriptRoot=/home/site/wwwroot \
    AzureFunctionsJobHost__Logging__Console__IsEnabled=true

EXPOSE 80
