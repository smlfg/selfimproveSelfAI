import sys
from selfai.config_loader import load_configuration, MiniMaxConfig
from selfai.core.agent import Agent

def main():
    """Main function to run the interactive agent chat."""
    print("Initializing SelfAI Agent...")
    try:
        # Load configuration
        config: MiniMaxConfig = load_configuration()
        print("✔️ Configuration loaded successfully.")

        # Initialize agent with the loaded configuration
        agent = Agent(config=config)
        print("🤖 Agent initialized. You can start chatting.")
        print("Type 'exit' or 'quit' to end the session.")

    except FileNotFoundError:
        print("❌ Failed to initialize agent: Configuration file 'config.yaml' not found.", file=sys.stderr)
        print("Please ensure your 'config.yaml' is set up correctly.", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"❌ Failed to initialize agent: {e}", file=sys.stderr)
        print("Please check your configuration file and environment variables.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ An unexpected error occurred during initialization: {e}", file=sys.stderr)
        sys.exit(1)


    while True:
        try:
            user_input = input("You: ").strip()
            if user_input.lower() in {"exit", "quit"}:
                print("Goodbye!")
                break
            
            if not user_input:
                continue

            agent_response = agent.run(user_input)
            print(f"Agent: {agent_response}")

        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
