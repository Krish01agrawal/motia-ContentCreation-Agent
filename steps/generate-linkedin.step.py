import os
import json
from pydantic import BaseModel, HttpUrl
from datetime import datetime
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

class GenerateInput(BaseModel):
    requestId: str
    url: HttpUrl
    title: str
    content: str
    timestamp: int

config = {
    'type': 'event',
    'name': 'LinkedinGenerate',
    'description': 'Generates LinkedIn content',
    'subscribes': ['generate-content'],
    'emits': ['linkedin-schedule'],
    'input': GenerateInput.model_json_schema(),
    'flows': ['content-generation']
}

async def handler(input, context):
    try:
        with open("prompts/linkedin-prompt.txt", "r", encoding='utf-8') as f:
            linkedinPromptTemplate = f.read()
        
        linkedinPrompt = linkedinPromptTemplate.replace('{{title}}', input['title']).replace('{{content}}', input['content'])

        context.logger.info("🔄 LinkedIn content generation started...")

        response = model.generate_content(linkedinPrompt)
        
        try:
            linkedin_content = json.loads(response.text)
        except Exception:
            linkedin_content = {'post': response.text}

        context.logger.info(f"🎉 LinkedIn content generated successfully!")

        await context.emit({
            'topic': 'linkedin-schedule',
            'data': {
                'requestId': input['requestId'],
                'url': input['url'],
                'title': input['title'],
                'content': linkedin_content,
                'generatedAt': datetime.now().isoformat(),
                'originalUrl': input['url']
            }
        })
    except Exception as e:
        context.logger.error(f"❌ Content generation failed: {e}")
        raise e