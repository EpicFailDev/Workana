
import warnings
try:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=FutureWarning)
        import google.generativeai as genai
    HAS_GENAI = True
except ImportError:
    genai = None
    HAS_GENAI = False

class GeminiFactory:
    @staticmethod
    def create(api_key: str, model_name: str = "gemini-3.6-flash"):
        if not HAS_GENAI:
            raise ImportError("Biblioteca 'google-generativeai' não está instalada.")
        
        genai.configure(api_key=api_key)
        return genai.GenerativeModel(model_name)
