#!/usr/bin/env python3
"""
Script simple para iniciar el servidor de datos meteorológicos.
"""
import sys
import os

# Agregar el directorio actual al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    print("🌤️  Iniciando Servicio de Datos Meteorológicos...")
    print("📍 Puerto: 8000")
    print("📚 Documentación: http://localhost:8000/docs")
    print("❤️  Health Check: http://localhost:8000/health")
    print("\n" + "="*50)
    
    try:
        import uvicorn
        from main import app
        
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8000,
            reload=True
        )
    except ImportError as e:
        print(f"❌ Error: {e}")
        print("\n📦 Instalando dependencias...")
        os.system("pip install fastapi uvicorn sqlalchemy psycopg2-binary pydantic python-dotenv httpx aiohttp")
        print("\n🔄 Reiniciando...")
        import uvicorn
        from main import app
        uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
    except Exception as e:
        print(f"❌ Error iniciando servidor: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 