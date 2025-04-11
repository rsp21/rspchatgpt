from services.openai_client import client

def transcribe_audio(file_stream):
    transcription = client.audio.transcriptions.create(
        model="gpt-4o-transcribe",
        file=file_stream
    )
    return transcription.text

def analyze_text(text):
    prompt = f"""
    Here is a transcription of an audio file:

    \"\"\"{text}\"\"\"

    1. What is the overall tone of the speaker? (e.g., friendly, professional, emotional, urgent)
    2. Provide a concise summary of what is being said.
    3. Include who the speaker is, where they are calling from, what they wanted.
    4. Include who the sales representative was and what was their tone and what they responded.
    """
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.5,
    )
    return response.choices[0].message.content
