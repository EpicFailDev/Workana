
try:
    import google.generativeai as genai
    HAS_GENAI = True
except ImportError:
    genai = None
    HAS_GENAI = False

class GeminiFactory:
    @staticmethod
    def create(api_key: str):
        if not HAS_GENAI:
            raise ImportError("Biblioteca 'google-generativeai' não está instalada.")
        
        genai.configure(api_key=api_key)
        return genai.GenerativeModel("gemini-2.5-flash")
