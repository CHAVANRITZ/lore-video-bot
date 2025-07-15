import importlib.util
import sys

# Force load genai from full path in Replit cache
genai_path = ".cache/uv/archive-v0/JwRqrSVtQbSsXV6XFweSD/google/genai/__init__.py"

try:
  spec = importlib.util.spec_from_file_location("google.genai", genai_path)
  genai = importlib.util.module_from_spec(spec)
  sys.modules["google.genai"] = genai
  spec.loader.exec_module(genai)

  print("✅ Gemini SDK is working!")
except Exception as e:
  print("❌ FAILED:", e)
