import fastapi
import uvicorn
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from .spotify import Spotify

class Client:
    def __init__(self, spotify: Spotify):
        self.spotify = spotify
        self.app = fastapi.FastAPI()
        self.app.mount("/static", StaticFiles(directory="static"), name="static")
        self._setup_routes()
    
    def _setup_routes(self):
        @self.app.get("/")
        async def index():
            return fastapi.responses.FileResponse("static/templates/index.html", media_type="text/html")
        
        #Base for future frontend impementation
        @self.app.get("/search/{uri}")
        async def search(uri: str):
            try:
                results = await self.spotify.search(uri)
                return results
            except Exception as e:
                return JSONResponse(status_code=500, content={"error": str(e)})
    
    def run(self, host: str = "0.0.0.0", port: int = 8000):
        uvicorn.run(self.app, host=host, port=port)