from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.requests import Request
import requests
import openai
import os

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="app/templates")

openai.api_key = os.getenv("OPENAI_API_KEY")
ocr_api_key = os.getenv("OCR_API_KEY")

def extrair_texto_via_ocr_space(image_bytes):
    url_api = "https://api.ocr.space/parse/image"
    response = requests.post(
        url_api,
        files={"filename": image_bytes},
        data={
            "apikey": ocr_api_key,
            "language": "por",
            "OCREngine": 2
        }
    )
    result = response.json()
    try:
        return result["ParsedResults"][0]["ParsedText"]
    except Exception:
        return "Erro ao extrair texto."

@app.get("/", response_class=HTMLResponse)
async def form_post(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/analisar")
async def analisar(request: Request, file: UploadFile = File(...)):
    contents = await file.read()
    texto_extraido = extrair_texto_via_ocr_space(contents)

    prompt = f'''
Você é um auditor técnico da ANVISA e MAPA. Analise o seguinte texto extraído de um rótulo de alimento e diga se está conforme com as normas brasileiras. Dê um parecer item por item, com base nas principais exigências (denominação, peso, alergênicos, validade, conservação, SIF, CNPJ, tabela nutricional, etc). Seja técnico e direto.

Texto extraído:
{texto_extraido}
'''

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
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
