import io
import zipfile

from fastapi import APIRouter, File, UploadFile, Query, HTTPException, Request
from fastapi.responses import Response, HTMLResponse
from PIL import Image

from backend.auth.login import require_login
from backend.services.denoise import denoise_image

router = APIRouter(prefix="/denoise", tags=["denoise"])


@router.post("/image")
async def denoise_single(
    request: Request,
    file: UploadFile = File(...),
    strength: float = Query(1.0, ge=0.0, le=5.0),
) -> Response:
    guard = require_login(request, "/denoise")
    if guard:
        return guard
    data = await file.read()
    img = Image.open(io.BytesIO(data)).convert("RGB")
    out = denoise_image(img, strength=strength)

    buf = io.BytesIO()
    out.save(buf, format="PNG")
    return Response(content=buf.getvalue(), media_type="image/png")


@router.post("/sequence.zip")
async def denoise_sequence_zip(
    request: Request,
    strength: float = Query(1.0, ge=0.0, le=5.0),
    files: list[UploadFile] = File(...),
) -> Response:
    guard = require_login(request, "/denoise")
    if guard:
        return guard
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded.")

    png_files = [f for f in files if (f.filename or "").lower().endswith(".png")]
    if not png_files:
        raise HTTPException(status_code=400, detail="No PNG files in upload.")

    zip_buf = io.BytesIO()
    with zipfile.ZipFile(zip_buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for f in png_files:
            data = await f.read()
            try:
                img = Image.open(io.BytesIO(data)).convert("RGB")
            except Exception as e:
                raise HTTPException(
                    status_code=400, detail=f"Failed to read image {f.filename}: {e}"
                )

            out = denoise_image(img, strength=strength)
            out_buf = io.BytesIO()
            out.save(out_buf, format="PNG")

            name = (f.filename or "frame.png").replace("\\", "/")
            arcname = "denoised/" + name
            arcname = arcname.rsplit(".", 1)[0] + ".png"
            zf.writestr(arcname, out_buf.getvalue())

    headers = {"Content-Disposition": 'attachment; filename="denoised_sequence.zip"'}
    return Response(zip_buf.getvalue(), media_type="application/zip", headers=headers)


# @router.post("/files/")
# async def create_files(files: Annotated[list[bytes], File()]):
#     return {"file_sizes": [len(file) for file in files]}
#
# @router.post("/uploadfiles/")
# async def create_upload_files(files: Annotated[list[UploadFile], File(...)]):
#     return {"filenames": [f.filename for f in files]}


@router.get("/")
async def denoise_page(request: Request):
    guard = require_login(request, "/denoise")
    if guard:
        return guard

    content = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <title>Denoise folder</title>
  <style>
    body { font-family: sans-serif; padding: 16px; }
    .row { margin: 10px 0; display: flex; gap: 10px; align-items: center; flex-wrap: wrap; }
    input[type="text"], input[type="number"] { padding: 6px; }
    button { padding: 8px 12px; cursor: pointer; }
    pre { background: #111; color: #0f0; padding: 10px; min-height: 140px; white-space: pre-wrap; }
    .muted { opacity: 0.7; }
  </style>
</head>
<body>
  <h2>Folder → PNG sequence → denoise → ZIP (server-side)</h2>

  <div class="row">
    <label><b>Select folder:</b></label>
    <input id="folder" type="file" webkitdirectory multiple />
  </div>

  <div class="row">
    <label class="muted">Strength:</label>
    <input id="strength" type="number" min="0" max="5" step="0.1" value="1.0" />
  </div>

  <div class="row">
    <button id="scan" type="button">Scan PNGs</button>
    <button id="run" type="button">Denoise + Download ZIP</button>
  </div>

  <pre id="log"></pre>

  <p><a href="/logout">Logout</a></p>

  <script>
    window.addEventListener("DOMContentLoaded", () => {
      const input = document.getElementById("folder");
      const strengthEl = document.getElementById("strength");
      const logEl = document.getElementById("log");
      const scanBtn = document.getElementById("scan");
      const runBtn = document.getElementById("run");

      function log(s) { logEl.textContent += s + "\\n"; }
      function clearLog() { logEl.textContent = ""; }

      function relPath(f) {
        return f.webkitRelativePath || f.name;
      }

      function collectPNGs(files) {
        const pngs = files.filter(f => /\\.png$/i.test(f.name));
        pngs.sort((a, b) => relPath(a).localeCompare(relPath(b)));
        return pngs;
      }

      function downloadBlob(blob, filename) {
        const a = document.createElement("a");
        const url = URL.createObjectURL(blob);
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        a.remove();
        URL.revokeObjectURL(url);
      }

      log("JS LOADED ✅");

      scanBtn.addEventListener("click", (e) => {
        e.preventDefault();
        try {
          clearLog();
          log("Scan clicked ✅");

          const files = Array.from(input.files || []);
          if (!files.length) return log("No folder selected.");

          const pngs = collectPNGs(files);
          log(`Selected files total: ${files.length}`);
          log(`PNG files found: ${pngs.length}`);
          log("First 10 PNGs:");
          for (const f of pngs.slice(0, 10)) log(`- ${relPath(f)}`);
        } catch (err) {
          console.error(err);
          log("ERROR in scan: " + (err?.message || err));
        }
      });

      runBtn.addEventListener("click", async (e) => {
        e.preventDefault();
        try {
          clearLog();
          log("Run clicked ✅");

          const files = Array.from(input.files || []);
          if (!files.length) return log("No folder selected.");

          const pngs = collectPNGs(files);
          if (!pngs.length) return log("No PNG files found.");

          const strength = parseFloat(strengthEl.value || "1.0");

          log(`PNG files: ${pngs.length}`);
          log(`Strength: ${strength}`);
          log(`Uploading ALL to POST /denoise/sequence.zip ...`);

          const form = new FormData();
          for (const f of pngs) {
            const name = relPath(f);
            form.append("files", f, name);
          }

          const url = `/denoise/sequence.zip?strength=${encodeURIComponent(strength)}`;
          const headers = {};

          const r = await fetch(url, { method: "POST", headers, body: form });

          log(`Response status: ${r.status}`);

          if (!r.ok) {
            const txt = await r.text().catch(() => "");
            log(`ERROR HTTP ${r.status}: ${txt}`);
            return;
          }

          const zipBlob = await r.blob();
          log(`ZIP size: ${zipBlob.size} bytes`);

          downloadBlob(zipBlob, "denoised_sequence.zip");
          log("Done. ZIP downloaded ✅");
        } catch (err) {
          console.error(err);
          log("ERROR in run: " + (err?.message || err));
        }
      });
    });
  </script>
</body>
</html>
    """
    return HTMLResponse(content=content)
