import config

def main():
    # Access API keys from config
    api_key = config.OPENAI_API_KEY
    
    # Example of using the API key
    print(f"Using API with endpoint: {config.API_ENDPOINT}")
    
    # Your application code here
    # ...

if __name__ == "__main__":
    main()