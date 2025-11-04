# Secrets and Configuration Management

This document outlines the standardized process for managing configuration and secrets within the SelfAI project. Following this process is critical for security and reproducibility.

## Core Principles

1.  **Separation of Concerns:** Secrets (like API keys) are kept separate from non-secret configuration (like model paths or parameters).
2.  **No Secrets in Git:** Under no circumstances should files containing secrets be committed to the repository.
3.  **Clear Templates:** Templates are provided to make setup for new developers easy and transparent.

## File Structure

-   `config.yaml`: **(Git Ignored)** Your local, non-secret configuration. You can freely change parameters here for your local setup.
-   `config.yaml.template`: **(Committed to Git)** A template showing the structure and available options for `config.yaml`.

-   `.env`: **(Git Ignored)** Your local file for storing secrets, specifically the `API_KEY`.
-   `.env.example`: **(Committed to Git)** An example file showing which environment variables are required.

-   `config_loader.py`: A Python module that loads, validates, and merges settings from both `config.yaml` and `.env` into a single, structured configuration object for the application.

## First-Time Setup Flow

If you are a new developer setting up the project, follow these steps:

1.  **Create `.env` file:**
    Copy the example file to create your local secrets file.
    ```bash
    cp .env.example .env
    ```

2.  **Edit `.env`:**
    Open the newly created `.env` file and replace `"your-anythingllm-api-key"` with your actual AnythingLLM Developer API Key.

3.  **Create `config.yaml`:**
    Copy the template to create your local configuration file.
    ```bash
    cp config.yaml.template config.yaml
    ```

4.  **Edit `config.yaml` (Optional):**
    You can now adjust parameters in `config.yaml`, such as changing the `model_path` for the CPU fallback or the `workspace_slug` for the NPU provider.

## Usage in Application Code

To access configuration values within the application, import and use the `load_configuration` function. It provides a validated, structured `AppConfig` object.

```python
from config_loader import load_configuration, AppConfig

try:
    config: AppConfig = load_configuration()
    print(f"Using model: {config.cpu_fallback.model_path}")
    # The API key is available via config.npu_provider.api_key
except (FileNotFoundError, ValueError) as e:
    print(f"Error loading configuration: {e}")
    # Handle error gracefully
```

This approach ensures that the rest of the application does not need to be aware of the different configuration sources and gets a clean, validated set of parameters to work with.
