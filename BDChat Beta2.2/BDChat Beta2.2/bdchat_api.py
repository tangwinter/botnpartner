from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import os
import re
import pandas as pd
from azure.ai.inference import ChatCompletionsClient
from azure.core.credentials import AzureKeyCredential
from azure.ai.inference.models import SystemMessage, UserMessage
import uvicorn

app = FastAPI()

# Allow CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
DEEPSEEK_API_KEY = "BM7BodPC9CVF8G1J0PD97KCFvcO9Tfdo5NxFEgci6TPjGfkL3EbYJQQJ99BDACYeBjFXJ3w3AAAAACOGGHm2"
DEEPSEEK_ENDPOINT = "https://ds32.services.ai.azure.com/models"
DEEPSEEK_MODEL = "deepseek-v3"

# Initialize the DeepSeek client
try:
    print("Initializing DeepSeek client...")
    client = ChatCompletionsClient(
        endpoint=DEEPSEEK_ENDPOINT,
        credential=AzureKeyCredential(DEEPSEEK_API_KEY),
    )
    print("DeepSeek client initialized successfully")
except Exception as e:
    print(f"Error initializing DeepSeek client: {str(e)}")
    client = None

class ResponseProcessor:
    """Handles the processing and formatting of LLM responses"""
    
    WARNING_MESSAGE = "\n\nWarning: The response above is given by our AI BD Manager powered by DeepSeek and there is no assurance that all information is accurate. If you need any legal advice, you should contact our lawyers."
    
    @staticmethod
    def format_response(response_text, selected_topics=None):
        """Format the response to add selected topics and warning message"""
        formatted = response_text.strip()
        
        # Convert markdown bold syntax to HTML
        formatted = formatted.replace('**', '<strong>')
        formatted = formatted.replace('*', '<em>')
        
        # Convert bullet points
        formatted = formatted.replace('- ', '<br>• ')
        formatted = formatted.replace('• ', '<br>• ')
        
        # Convert numbered lists
        formatted = re.sub(r'(\d+)\. ', r'<br>\1. ', formatted)
        
        # Convert double newlines to paragraph breaks
        formatted = formatted.replace('\n\n', '</p><p>')
        
        # Wrap the entire response in paragraph tags
        formatted = f'<p>{formatted}</p>'
        
        # Add selected topics if provided
        if selected_topics and len(selected_topics) > 0:
            formatted += f'<p>Selected Topics: {", ".join(selected_topics)}</p>'
        
        # Add the warning message
        formatted += f'<p>{ResponseProcessor.WARNING_MESSAGE}</p>'
        
        return formatted

    @staticmethod
    def process_response(response_text, selected_topics=None):
        """Main method to process and format the response"""
        if not response_text:
            return "We have come across a technical problem. Please ask again. Apologies."
            
        # Format the response with topics and warning
        return ResponseProcessor.format_response(response_text, selected_topics)

    @staticmethod
    def extract_top_topics(response_text):
        """Extract the top 3 topics from the LLM response"""
        if not response_text:
            return []
            
        # Split into lines and look for topic indicators
        lines = response_text.split('\n')
        topics = []
        
        for line in lines:
            # Clean the line
            line = line.strip()
            
            # Skip empty lines
            if not line:
                continue
                
            # Look for numbered topics (1., 2., 3.)
            match = re.match(r'^\d+\.\s*(.+)$', line)
            if match:
                topic = match.group(1).strip()
                # Remove any remaining numbers or special characters at the start
                topic = re.sub(r'^[\d\s\.]+', '', topic).strip()
                # Remove any square brackets if present
                topic = re.sub(r'^\[|\]$', '', topic).strip()
                if topic:
                    topics.append(topic)
        
        # If we didn't find any topics, try a more lenient approach
        if not topics:
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                    
                # Try to find any line that looks like a topic
                if re.match(r'^[A-Za-z]', line):  # Starts with a letter
                    # Remove any leading numbers, dots, or brackets
                    topic = re.sub(r'^[\d\.\s\[\]]+', '', line).strip()
                    if topic and len(topic) > 3:  # Ensure it's not too short
                        topics.append(topic)
        
        # Ensure we have exactly 3 topics
        if len(topics) > 3:
            topics = topics[:3]
        elif len(topics) < 3:
            # Pad with empty strings if we have fewer than 3 topics
            topics.extend([''] * (3 - len(topics)))
            
        return topics

# System prompts
TOPIC_IDENTIFICATION_PROMPT = """You are an experienced legal practitioner in Hong Kong. Given a list of legal topics and a question, you MUST select the top 3 most relevant topics that would help answer the question.

Available topics:
{topics}

Question: {question}

List ONLY the top 3 most relevant topics in order of relevance, numbered 1-3. Do not include any other text or explanation."""

SYSTEM_PROMPT = """You are an experienced business development manager of a law firm but you are not a qualified lawyer. Your role is to provide helpful, professional guidance to clients and, very importantly to provide fee range for clients' reference.  Your job is to market your firm's service and drive business.

Key guidelines:
1. You should derive your response from the content of the FAQs.  You can expand the meaning of the FAQ naturally. 
2. Respond directly and conversationally, as if speaking from your own experience, but never mention about the existence of the FAQs.
3. Provide practical examples and general guidance when appropriate
4. Avoid giving specific legal advice nor solid suggestions on how the matter should be structure nor the detailed steps.  Use examples if you want to give suggestions, (e.g. depending on the client's circumstances, we may suggest [], but this would depend on your objective and our lawyer needs to have more details from you to provided with any recommendation that suits your need")
5. Always try to explain how your lawyers can help the user and provide a fee range.  If you don't find a fee range for the exact kind of work asked by the client, you should read in the context of the relevant FAQ and provide the standard work and fee range provided in there.
6. If you want to say something but consider that it may be inappropriate to say so given the guidance above, try to say what is already provided in the relevant FAQ.  Don't stop without finishing what you are saying.
7. Always include an email address for the client to contact your firm if you are asking whether client would like you to connect him with your lawyers (e.g. "If you would like us to connect you with our specialist, please email us on: [email address]").
8. Always add a + sign at the top end of the fee range (e.g. "HK$10,000 to HK$15,000+") to leave room for your lawyers to quote higher fees in a complicated case

Remember: You are speaking as an experienced manager, not as an AI or documentation system. Your responses should reflect your expertise and experience in the field."""

# Load FAQ dataset
def load_faq_dataset():
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        excel_path = os.path.join(script_dir, "(Bot4Pro) Simulated FAQ Dataset (with topic).xlsx")
        df = pd.read_excel(excel_path, header=None)
        df = df.iloc[:, :2]
        df.columns = ['Topic', 'FAQ_Content']
        df['Topic'] = df['Topic'].apply(lambda x: re.sub(r'\*\*|\*', '', str(x)).strip())
        return df
    except Exception as e:
        print(f"Error loading FAQ dataset: {str(e)}")
        return None

faq_df = load_faq_dataset()

@app.post("/chat")
async def chat(request: Request):
    try:
        if client is None:
            return {"error": "Chat service is not properly initialized. Please try again later."}
            
        data = await request.json()
        user_message = data.get("message", "")
        
        if not user_message:
            return {"error": "No message provided"}

        # Get relevant topics
        topics = faq_df['Topic'].tolist()
        topic_prompt = TOPIC_IDENTIFICATION_PROMPT.format(
            topics='\n'.join(topics),
            question=user_message
        )
        
        try:
            topic_response = client.complete(
                model=DEEPSEEK_MODEL,
                messages=[
                    SystemMessage(content=topic_prompt),
                    UserMessage(content=user_message)
                ]
            )
            
            selected_topics = ResponseProcessor.extract_top_topics(topic_response.choices[0].message.content)
            
            # Get chatbot response
            response = client.complete(
                model=DEEPSEEK_MODEL,
                messages=[
                    SystemMessage(content=SYSTEM_PROMPT),
                    UserMessage(content=user_message)
                ]
            )
            
            formatted_response = ResponseProcessor.process_response(
                response.choices[0].message.content,
                selected_topics
            )
            
            return {"response": formatted_response}
            
        except Exception as e:
            print(f"Error in chat API call: {str(e)}")
            return {"error": "Unable to connect to chat service. Please try again later."}
        
    except Exception as e:
        print(f"Error in chat endpoint: {str(e)}")
        return {"error": "An error occurred while processing your request"}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000) 