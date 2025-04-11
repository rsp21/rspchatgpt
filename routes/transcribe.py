from flask import Blueprint, request, jsonify
from services.transcription_service import transcribe_audio, analyze_text
import io

transcribe_bp = Blueprint('transcribe', __name__)

@transcribe_bp.route("/transcribe", methods=["POST"])
def transcribe_and_analyze():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    audio_file = request.files['file']
    file_stream = io.BytesIO(audio_file.read())

    try:
        transcript = transcribe_audio(file_stream)
        analysis = analyze_text(transcript)
        return jsonify({
            "transcription": transcript,
            "analysis": analysis
        })
    except Exception as e:
        return jsonify({"error ": str(e)}), 500
