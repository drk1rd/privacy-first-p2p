from fastapi import FastAPI, UploadFile, Form, Request
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from tempfile import NamedTemporaryFile
import shutil, json, os
from encryption_utils import load_private_key, decrypt_key_with_rsa, decrypt_and_reconstruct
import socket

app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

PORT = 3500

class SocketDHT:
  def __init__(self, real_hashes, ip):
    self.cache = {}
    self.real_hashes = set(real_hashes)
    self.ip = ip

  def retrieve(self, chunk_hash):
    if chunk_hash not in self.real_hashes:
      return None
    if chunk_hash in self.cache:
      return self.cache[chunk_hash]

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
      s.connect((self.ip, 5000))
      s.sendall(json.dumps({ "hash": chunk_hash }).encode())
      response = s.recv(65536).decode()
      reply = json.loads(response)
      if reply.get("status") == "OK":
        self.cache[chunk_hash] = reply["chunk"]
        return reply["chunk"]
    return None


@app.get("/", response_class=HTMLResponse)
async def homepage(request: Request):
  return templates.TemplateResponse("client_index.html", {"request": request})


@app.post("/submit-manifest")
async def submit_manifest(
  request: Request,
  manifest: UploadFile,
  privkey: UploadFile,
  server_ip: str = Form(...)
):
  try:
    with NamedTemporaryFile(delete=False) as mfile, NamedTemporaryFile(delete=False) as kfile:
      shutil.copyfileobj(manifest.file, mfile)
      shutil.copyfileobj(privkey.file, kfile)
      manifest_path = mfile.name
      priv_key_path = kfile.name

    output_path = "received_output_from_peer"  # Can be auto-named too

    with open(manifest_path, "r") as f:
      manifest_data = json.load(f)

    priv_key = load_private_key(priv_key_path)
    aes_key = decrypt_key_with_rsa(priv_key, bytes.fromhex(manifest_data["encrypted_key"]))

    dht = SocketDHT(manifest_data["chunks"], server_ip)
    output_file_path = os.path.join("received_files", "RECEIVED_" + manifest_data["filename"])
    os.makedirs("received_files", exist_ok=True)

    decrypt_and_reconstruct(manifest_data, aes_key, dht, output_file_path)

    return templates.TemplateResponse("client_success.html", {
      "request": request,
      "msg": "File reconstructed successfully!",
      "filepath": output_file_path
    })

  except Exception as e:
    return templates.TemplateResponse("client_error.html", {
      "request": request,
      "msg": f"Error: {e}"
    })


@app.get("/download")
async def download(filepath: str):
  return FileResponse(filepath, filename=os.path.basename(filepath), media_type='application/octet-stream')
