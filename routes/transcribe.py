from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from services.transcription_service import transcribe_audio, analyze_text
from services.downloader_8 import download_main
import io
import zipfile
import os
import tempfile

transcribe_bp = Blueprint('transcribe', __name__)

@transcribe_bp.route("/transcribe", methods=["GET"])
@login_required
def transcribe_and_analyze():
    try:
        actual_user_id = current_user.get_actual_id()
        print(f"🔐 Transcribing for user actual ID: {actual_user_id}")

        zip_path = download_main(actual_user_id)
        print(f"📦 Downloaded ZIP: {zip_path}")

        with tempfile.TemporaryDirectory() as temp_dir:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)

            audio_path = None
            for root, _, files in os.walk(temp_dir):
                for file in files:
                    if file.lower().endswith(('.mp3', '.wav')):
                        audio_path = os.path.join(root, file)
                        break
                if audio_path:
                    break

            if not audio_path:
                return jsonify({"error": "No audio file found in the ZIP"}), 400

            with open(audio_path, 'rb') as f:
                audio_stream = io.BytesIO(f.read())

        transcript = transcribe_audio(audio_stream, filename=os.path.basename(audio_path))

        # Get prompt from request args
        custom_prompt = request.args.get("prompt", "").strip()
        prompt_to_use = custom_prompt if custom_prompt else ""

        analysis = analyze_text(transcript, default_prompt=prompt_to_use)

        return jsonify({
            "transcription": transcript,
            "analysis": analysis
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500
