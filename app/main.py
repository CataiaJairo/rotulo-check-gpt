from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.requests import Request
import pytesseract
from PIL import Image
import io
import openai
import os

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="app/templates")

openai.api_key = os.getenv("OPENAI_API_KEY")

@app.get("/", response_class=HTMLResponse)
async def form_post(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/analisar")
async def analisar(request: Request, file: UploadFile = File(...)):
    contents = await file.read()
    image = Image.open(io.BytesIO(contents))
    texto_extraido = pytesseract.image_to_string(image)

    prompt = f"""
Você é um auditor técnico da ANVISA e MAPA. Analise o seguinte texto extraído de um rótulo de alimento e diga se está conforme com as normas brasileiras. Dê um parecer item por item, com base nas principais exigências (denominação, peso, alergênicos, validade, conservação, SIF, CNPJ, tabela nutricional, etc). Seja técnico e direto.

Texto extraído:
{texto_extraido}
"""


    response = openai.ChatCompletion.create(
        model="gpt-4-turbo",
        messages=[
            {"role": "system", "content": "Você é um especialista em rotulagem técnica de alimentos no Brasil."},
            {"role": "user", "content": prompt}
        ]
    )

    resultado = response.choices[0].message.content
    return templates.TemplateResponse("index.html", {
        "request": request,
        "resultado": resultado,
        "texto_extraido": texto_extraido
    })
