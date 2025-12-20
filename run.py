#!/usr/bin/env python3
"""
FinanceGhost Autonomous - Run Script
Starts both backend and provides frontend instructions
"""

import subprocess
import sys
import os

def main():
    print("""
╔═══════════════════════════════════════════════════════════════════╗
║                                                                   ║
║   ███████╗██╗███╗   ██╗ █████╗ ███╗   ██╗ ██████╗███████╗        ║
║   ██╔════╝██║████╗  ██║██╔══██╗████╗  ██║██╔════╝██╔════╝        ║
║   █████╗  ██║██╔██╗ ██║███████║██╔██╗ ██║██║     █████╗          ║
║   ██╔══╝  ██║██║╚██╗██║██╔══██║██║╚██╗██║██║     ██╔══╝          ║
║   ██║     ██║██║ ╚████║██║  ██║██║ ╚████║╚██████╗███████╗        ║
║   ╚═╝     ╚═╝╚═╝  ╚═══╝╚═╝  ╚═╝╚═╝  ╚═══╝ ╚═════╝╚══════╝        ║
║                                                                   ║
║   ██████╗ ██╗  ██╗ ██████╗ ███████╗████████╗                     ║
║   ██╔════╝ ██║  ██║██╔═══██╗██╔════╝╚══██╔══╝                     ║
║   ██║  ███╗███████║██║   ██║███████╗   ██║                        ║
║   ██║   ██║██╔══██║██║   ██║╚════██║   ██║                        ║
║   ╚██████╔╝██║  ██║╚██████╔╝███████║   ██║                        ║
║    ╚═════╝ ╚═╝  ╚═╝ ╚═════╝ ╚══════╝   ╚═╝                        ║
║                                                                   ║
║   🤖 AUTONOMOUS AI - Invoice Processing System                   ║
║                                                                   ║
╚═══════════════════════════════════════════════════════════════════╝
    """)
    
    print("🚀 Starting FinanceGhost Autonomous...")
    print()
    print("📦 Backend: FastAPI + Python")
    print("🎨 Frontend: Vite + React + TypeScript")
    print("🤖 AI: Vertex AI Gemini / OpenAI GPT-4")
    print()
    print("=" * 60)
    print()
    
    # Check environment
    if not os.path.exists(".env"):
        print("⚠️  No .env file found. Copying from .env.example...")
        if os.path.exists(".env.example"):
            import shutil
            shutil.copy(".env.example", ".env")
            print("   Created .env file. Please configure your API keys.")
    
    print("📝 To run the full application:")
    print()
    print("   Terminal 1 (Backend):")
    print("   ─────────────────────")
    print("   cd financeghost")
    print("   python -m venv venv")
    print("   source venv/bin/activate")
    print("   pip install -r requirements.txt")
    print("   uvicorn app.main:app --reload --port 8000")
    print()
    print("   Terminal 2 (Frontend):")
    print("   ───────────────────────")
    print("   cd financeghost/frontend")
    print("   bun run dev")
    print()
    print("=" * 60)
    print()
    print("🌐 URLs:")
    print("   Backend API:  http://localhost:8000")
    print("   API Docs:     http://localhost:8000/docs")
    print("   Frontend:     http://localhost:5173")
    print("   Demo:         http://localhost:8000/demo")
    print()
    print("=" * 60)
    
    # Ask if user wants to start backend
    try:
        response = input("\n🤔 Start backend server now? [Y/n]: ").strip().lower()
        if response in ["", "y", "yes"]:
            print("\n🚀 Starting backend server on port 8000...")
            print("   Press Ctrl+C to stop\n")
            subprocess.run([
                sys.executable, "-m", "uvicorn",
                "app.main:app",
                "--reload",
                "--host", "0.0.0.0",
                "--port", "8000"
            ])
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")


if __name__ == "__main__":
    main()
