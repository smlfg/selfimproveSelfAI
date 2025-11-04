# Base Image: Python 3.12 (CPU-first)
FROM mcr.microsoft.com/devcontainers/python:3.12

# Install build tools required for llama-cpp-python and other dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake
