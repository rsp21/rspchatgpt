import logging
import traceback
from services.openai_client import client

# Configure logging (you can adjust level and format as needed)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def transcribe_audio(file_stream, filename="audio.wav"):
    try:
        # Determine MIME type based on extension
        mime_type = "audio/wav" if filename.endswith(".wav") else "audio/mpeg"
        
        # Send to OpenAI Whisper API
        transcription = client.audio.transcriptions.create(
            model="whisper-1",
            file=(filename, file_stream, mime_type),
            temperature=0.5
        )

        # Safeguard: make sure transcription has 'text'
        if hasattr(transcription, "text") and transcription.text:
            return str(transcription.text)
        else:
            raise ValueError("Transcription returned no text.")
    
    except Exception as e:
        logger.error(f"[Transcription Error] {str(e)}")
        logger.debug(traceback.format_exc())
        raise RuntimeError("Failed to transcribe audio. Check logs for details.") from e

def analyze_text(text, default_prompt=None):
    try:
        if not default_prompt:
            default_prompt = '''
            1. What is the overall tone of the speaker? (e.g., friendly, professional, emotional, urgent)
            2. Provide a concise summary of what is being said.
            3. Include who the speaker is, where they are calling from, what they wanted.
            4. Include who the sales representative was and what was their tone and what they responded.
            '''

        prompt = f"""
        Here is a transcription of an audio file:

        \"\"\"{text}\"\"\"

        {default_prompt}
        """

        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5
        )

        return response.choices[0].message.content

    except Exception as e:
        logger.error(f"[Text Analysis Error] {str(e)}")
        logger.debug(traceback.format_exc())
        raise RuntimeError("Failed to analyze text. Check logs for details.") from e
