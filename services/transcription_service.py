from services.openai_client import client

def transcribe_audio(file_stream, filename="audio.wav"):
    # Determine MIME type based on extension
    mime_type = "audio/wav" if filename.endswith(".wav") else "audio/mpeg"
    
    # Send to OpenAI Whisper API
    transcription = client.audio.transcriptions.create(
        model="whisper-1",
        file=(filename, file_stream, mime_type)
    )
    return transcription.text

def analyze_text(text, default_prompt):

    if default_prompt == "":
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
        temperature=0.5,
    )
    return response.choices[0].message.content
