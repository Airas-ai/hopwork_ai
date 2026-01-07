import google.generativeai as genai

# Replace with your actual API key
genai.configure(api_key="AIzaSyCahvV9UtUg9LFlUfkLP8rcNulkjOx5wcc")

try:
    models = genai.list_models()

    print("Available Gemini models for this API key:\n")

    for model in models:
        print(f"Model name: {model.name}")
        print(f"Supported methods: {model.supported_generation_methods}")
        print("-" * 50)

except Exception as e:
    print("Error listing models:", str(e))
