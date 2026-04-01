"""
Startup diagnostics for StudyRAG.
Run from the studyrag/ root: python debug_startup.py
"""
import os
import sys
from pathlib import Path

SEP = "-" * 55

def ok(msg): print(f"  [OK]  {msg}")
def fail(msg): print(f"  [FAIL] {msg}")
def info(msg): print(f"  [..] {msg}")

# ── 1. Working directory & .env ──────────────────────────
print(SEP)
print("1. ENVIRONMENT")
cwd = Path.cwd()
info(f"cwd: {cwd}")

env_path = cwd / ".env"
if env_path.exists():
    ok(f".env found at {env_path}")
else:
    fail(f".env NOT found at {env_path}")
    print("     → Create .env (copy from .env.example) in the studyrag/ folder")

# ── 2. Config / model path ───────────────────────────────
print(SEP)
print("2. CONFIG")
try:
    from src.config import Settings
    s = Settings()
    info(f"llm_model_path (raw):     {s.llm_model_path}")
    model_path = Path(s.llm_model_path)
    model_abs  = (cwd / model_path).resolve()
    info(f"llm_model_path (abs):     {model_abs}")
    if model_abs.exists():
        size_gb = model_abs.stat().st_size / 1e9
        ok(f"Model file found ({size_gb:.2f} GB)")
    else:
        fail(f"Model file NOT found: {model_abs}")
        # list what IS in models/
        models_dir = cwd / "models"
        if models_dir.exists():
            files = list(models_dir.iterdir())
            info(f"Files in models/: {[f.name for f in files]}")
        else:
            fail("models/ directory does not exist")
except Exception as e:
    fail(f"Config load failed: {e}")
    sys.exit(1)

# ── 3. llama-cpp-python ──────────────────────────────────
print(SEP)
print("3. LLAMA-CPP-PYTHON")
llama_cpp_ok = False
try:
    import llama_cpp
    ok(f"llama_cpp imported (version: {getattr(llama_cpp, '__version__', 'unknown')})")
    llama_cpp_ok = True

    # Check GPU offload support (llama_cpp >= 0.2.x)
    try:
        gpu_ok = llama_cpp.llama_supports_gpu_offload()
        if gpu_ok:
            ok("llama_cpp reports GPU offload supported")
        else:
            fail("llama_cpp reports GPU offload NOT supported (CPU-only build)")
            info("To fix: pip install llama-cpp-python --force-reinstall --no-cache-dir")
            info("  with env var: CMAKE_ARGS=-DGGML_CUDA=on  (Windows: set CMAKE_ARGS=-DGGML_CUDA=on)")
    except AttributeError:
        info("Could not call llama_supports_gpu_offload() – skipping GPU build check")
except ImportError as e:
    fail(f"llama_cpp not installed: {e}")
    sys.exit(1)

# ── 4. Attempt model load ────────────────────────────────
print(SEP)
print("4. MODEL LOAD")
if llama_cpp_ok and model_abs.exists():
    from llama_cpp import Llama

    # 4a – CPU baseline (n_gpu_layers=0)
    try:
        llm = Llama(model_path=str(model_abs), n_gpu_layers=0, n_ctx=512, verbose=False)
        ok("CPU load (n_gpu_layers=0): success")
        del llm
    except Exception as e:
        fail(f"CPU load FAILED: {e}")

    # 4b – GPU mode (n_gpu_layers=-1) — this is what the server uses
    try:
        llm = Llama(model_path=str(model_abs), n_gpu_layers=-1, n_ctx=512, verbose=False)
        ok("GPU load (n_gpu_layers=-1): success")
        del llm
    except Exception as e:
        fail(f"GPU load (n_gpu_layers=-1) FAILED: {e}")
        info("Server will fail to load LLM for this same reason")
        info("Fix: set LLM_N_GPU_LAYERS=0 in .env to force CPU mode")
else:
    info("Skipped – llama_cpp or model not available")

# ── 5. PyTorch / CUDA ────────────────────────────────────
print(SEP)
print("5. PYTORCH / CUDA")
try:
    import torch
    ok(f"torch {torch.__version__}")
    if torch.cuda.is_available():
        ok(f"CUDA available – {torch.cuda.get_device_name(0)}")
    else:
        fail("torch.cuda.is_available() = False")
        info(f"torch build: {torch.version.cuda}")
        if torch.version.cuda is None:
            info("CPU-only PyTorch installed. Reinstall with CUDA:")
            info("pip install torch --index-url https://download.pytorch.org/whl/cu121")
except ImportError:
    fail("torch not installed")

print(SEP)
print("Done. Fix any [FAIL] items above and restart the server.")
