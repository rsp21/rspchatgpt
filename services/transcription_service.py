import logging
import traceback
from services.openai_client import client

# Configure logging (you can adjust level and format as needed)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
import os

def transcribe_audio(file_stream, user_id,filename="audio.wav"):
    try:
        # Determine MIME type
        mime_type = "audio/wav" if filename.endswith(".wav") else "audio/mpeg"

        # Transcribe with Whisper
        transcription = client.audio.transcriptions.create(
            model="whisper-1",
            file=(filename, file_stream, mime_type),
            temperature=0.5
        )

        if hasattr(transcription, "text") and transcription.text:
            text = str(transcription.text)

            # Save transcription with consistent name
            output_dir =f"transcriptions/{user_id}"
            os.makedirs(output_dir, exist_ok=True)

            output_path = os.path.join(output_dir, "latest_transcription.txt")

            # Overwrite existing file
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(text)

            return text

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
            1. Analize the call give the the tone of the call and the summary.
            2. I’d like you to create a strong follow-up call script I can use to deepen the relationship, make the contact feel more personally connected to me, and position RSP Supply as a trusted, go-to supplier—especially for hard-to-find or critical components. The goal is to uncover new opportunities by asking smart, open-ended questions that help me better understand how I can support their work and solve pain points. The script should feel natural, personable, and confident—showing that I’m resourceful, competent, and here to make their job easier.
            '''

        prompt = f"""
        Here is a transcription of an audio file:

        \"\"\"{text}\"\"\"
        And this is what I want you to do:
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
