from app.main import app

# Esto es necesario para que Vercel pueda manejar la aplicación FastAPI

# No es necesario crear una nueva instancia de FastAPI,
# simplemente exporta la que ya tienes
app = app