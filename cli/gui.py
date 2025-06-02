from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse,FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os
import json
import shutil
from tempfile import NamedTemporaryFile
from encryption_utils import (generate_rsa_keypair_gui,load_public_key,
  encrypt_key_with_rsa,
  chunk_and_encrypt)
from p2p_node import DHT
from fastapi import UploadFile, File
import threading
from peer_server import start_server

dht = DHT()
app = FastAPI()

@app.post("/upload", response_class=FileResponse)
async def upload_file(file: UploadFile = File(...), pubkey: UploadFile = File(...)):

    with NamedTemporaryFile(delete=False) as temp_file, NamedTemporaryFile(delete=False) as temp_pubkey:
        shutil.copyfileobj(file.file, temp_file)
        shutil.copyfileobj(pubkey.file, temp_pubkey)
        file_path = temp_file.name
        pubkey_path = temp_pubkey.name

    pub_key = load_public_key(pubkey_path)
    aes_key, manifest = chunk_and_encrypt(file_path)
    manifest["encrypted_key"] = encrypt_key_with_rsa(pub_key, aes_key).hex()
    for h, chunk_data in manifest["chunk_data"].items():
        dht.store(h, chunk_data)

    manifest_path = file_path + "_manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(manifest, f)

    return FileResponse(manifest_path, filename="manifest.json", media_type="application/json")


app.mount("/static", StaticFiles(directory="static"), name="static")


templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
async def item(request: Request):
    return templates.TemplateResponse("index.html",
        {"request":request}
    )


@app.get("/generate-keys", response_class=HTMLResponse)
async def generate_keys(request:Request):
    generate_rsa_keypair_gui()
    return templates.TemplateResponse("keys_ready.html", {"request": request})

@app.get("/download/private-key")
async def download_private_key():
  return FileResponse("generated/my_private.pem", filename="my_private.pem", media_type='application/octet-stream')

@app.get("/download/public-key")
async def download_public_key():
  return FileResponse("generated/my_public.pem", filename="my_public.pem", media_type='application/octet-stream')
    
logs=[]
active_server = False
@app.post("/start-chunk-server")
async def start_chunk_server(request: Request):
    form = await request.form()
    manifest_path = form.get("manifest_path")

    if not os.path.exists(manifest_path):
        return templates.TemplateResponse("error.html", {
            "request": request,
            "msg": "Manifest file not found!"
        })
    logs.clear()
    active_server=True
    threading.Thread(target=start_server, args=(manifest_path,logs), daemon=True).start()

    return templates.TemplateResponse("success.html", {
        "request": request,
        "msg": f"Chunk server started on port 5000 with {manifest_path}",
        "logs":logs
    })

@app.get("/view-active-server-log")
async def view_active_server(request: Request):
    return templates.TemplateResponse("success.html", {
        "request": request,
        "msg": "Chunk server is still running...",
        "logs": logs
    })
@app.post("/view-logs")
async def view_logs(request: Request):
    return templates.TemplateResponse("success.html", {
        "request": request,
        "msg": "Chunk server is still running...",
        "logs": logs
    })