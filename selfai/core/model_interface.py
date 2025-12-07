from typing import List, Dict
from openai import OpenAI
from selfai.config_loader import PlannerProviderConfig # Import the dataclass for type hinting

# A message is a dictionary with a role and content
Message = Dict[str, str]

class ModelInterface:
    """A generic interface to communicate with an OpenAI-compatible LLM."""
    def __init__(self, provider_config: PlannerProviderConfig):
        """Initialize the model interface with a specific provider's configuration."""
        
        if not provider_config:
            raise ValueError("A valid provider_config must be supplied to ModelInterface.")

        self.model = provider_config.model
        base_url = provider_config.base_url
        
        # The config loader resolves API keys into the headers dictionary.
        # The OpenAI client can take a default_headers argument.
        self.client = OpenAI(base_url=base_url, api_key="not-needed", default_headers=provider_config.headers)

    def chat_completion(self, messages: List[Message], temperature: float = 0.1) -> str:
        """Send messages to the language model and get a response."""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                # We ask for a JSON response, but will handle cases where it's not.
                response_format={"type": "json_object"} 
            )
            # Check for None response before accessing attributes
            if response and response.choices and response.choices[0].message:
                return response.choices[0].message.content or ""
            return "Error: Received an empty response from the model."
        except Exception as e:
            print(f"[ModelInterface] Error calling LLM: {e}")
            # Return a stringified error to be handled by the agent
            return f"Error communicating with the model: {e}"