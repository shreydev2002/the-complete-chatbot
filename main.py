# from urllib.request import Request

from openai import OpenAI
from fastapi import FastAPI, Form, Request, WebSocket   #Form bcz when we create our POST request, we are going to submit the question or the user input through a form inside our body of our post request
from typing import Annotated
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import os
from dotenv import load_dotenv

load_dotenv()

openai = OpenAI(
    api_key= os.getenv('OPENAI_API_SECRET_KEY')
)
app=FastAPI()
templates = Jinja2Templates(directory="templates")      #it says that our Jinja2 templates will be located inside our directory of templates

chat_responses = []
@app.get("/", response_class=HTMLResponse)
async def chat_page(request: Request):
    chat_responses.clear()  #Clear global chat history
    return templates.TemplateResponse("home.html", {"request": request, "chat_responses": chat_responses})


chat_log = [{'role': 'system', 'content': 'You are a helpful assistant'}]


@app.websocket("/ws")
async def chat(websocket: WebSocket):
    await websocket.accept()
    while True:
        user_input = await websocket.receive_text()
        chat_log.append({'role':'user', 'content' : user_input})
        chat_responses.append(user_input)

        try:
            response = openai.chat.completions.create(
                model= "gpt-4",
                messages = chat_log,
                temperature = 0.6,
                stream = True
            )
            ai_response = ''

            for chunk in response:
                if chunk.choices[0].delta.content is not None:
                    ai_response += chunk.choices[0].delta.content
                    await websocket.send_text(chunk.choices[0].delta.content)

            chat_responses.append(ai_response)
        except Exception as e:
            await websocket.send_text(f"Error: {str(e)}")
            break

@app.post("/", response_class=HTMLResponse)
async def chat(request: Request ,user_input: Annotated[str, Form()]):
    chat_log.append({'role': 'user', 'content': user_input})
    chat_responses.append(user_input)

    response = openai.chat.completions.create(
        model='gpt-3.5-turbo',
        messages = chat_log,
        temperature=0.5
    )

    bot_response = response.choices[0].message.content
    chat_log.append({'role': 'assistant', 'content': bot_response})
    chat_responses.append(bot_response)
    return templates.TemplateResponse("home.html", {"request": request, "chat_responses": chat_responses})



@app.get("/image", response_class= HTMLResponse)
async def image_page(request:Request):
    return templates.TemplateResponse("image.html", {"request": request})


@app.post("/image", response_class= HTMLResponse)
async def create_image(request: Request, user_input : Annotated[str, Form()]):
    response = openai.images.generate(
        prompt = user_input,
        n = 1,
        size = "256x256"
    )
    
    image_url = response.data[0].url
    return templates.TemplateResponse("image.html", {"request" : request, "image_url" : image_url})

