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
    'name': 'TwitterGenerate',
    'description': 'Generates Twitter content',
    'subscribes': ['generate-content'],
    'emits': ['twitter-schedule'],
    'input': GenerateInput.model_json_schema(),
    'flows': ['content-generation']
}

async def handler(input, context):
    try:
        with open("prompts/twitter-prompt.txt", "r", encoding='utf-8') as f:
            twitterPromptTemplate = f.read()
        
        twitterPrompt = twitterPromptTemplate.replace('{{title}}', input['title']).replace('{{content}}', input['content'])

        context.logger.info("🔄 Twitter content generation started...")

        response = model.generate_content(twitterPrompt)
        
        try:
            twitter_content = json.loads(response.text)
        except Exception:
            twitter_content = {'thread': [{'tweetNumber': 1, 'content': response.text}]}

        context.logger.info(f"🎉 Twitter content generated successfully!")

        await context.emit({
            'topic': 'twitter-schedule',
            'data': {
                'requestId': input['requestId'],
                'url': input['url'],
                'title': input['title'],
                'content': twitter_content,
                'generatedAt': datetime.now().isoformat(),
                'originalUrl': input['url']
            }
        })
    except Exception as e:
        context.logger.error(f"❌ Content generation failed: {e}")
        raise e