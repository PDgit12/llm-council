import requests
import json

def list_free_models():
    try:
        response = requests.get("https://openrouter.ai/api/v1/models")
        response.raise_for_status()
        models = response.json().get('data', [])
        
        free_models = []
        for m in models:
            # Check for free pricing (some might be effectively free but not marked 0, but let's look for explicit 0)
            # The API returns 'pricing': {'prompt': '...', 'completion': '...'}
            pricing = m.get('pricing', {})
            prompt = pricing.get('prompt', '1')
            completion = pricing.get('completion', '1')
            
            if prompt == '0' and completion == '0':
                free_models.append(m['id'])
            elif m['id'].endswith(':free'):
                free_models.append(m['id'])
                
        print(f"Found {len(free_models)} free models:")
        for mid in sorted(free_models):
            print(f"- {mid}")
            
    except Exception as e:
        print(f"Error fetching models: {e}")

if __name__ == "__main__":
    list_free_models()
