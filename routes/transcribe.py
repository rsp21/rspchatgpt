from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from services.transcription_service import transcribe_audio, analyze_text
from services.downloader_8 import download_main, get_calls, download_single
import io
import zipfile
import os
import tempfile
from datetime import datetime

transcribe_bp = Blueprint('transcribe', __name__)

@transcribe_bp.route("/transcribe", methods=["GET"])
@login_required
def transcribe_and_analyze():
    try:
        actual_user_id = current_user.get_actual_id()
        print(f"🔐 Transcribing for user actual ID: {actual_user_id}")

        zip_path = download_main(actual_user_id)
        print(f"📦 Downloaded ZIP path: {zip_path}")

        if not zip_path:
            return jsonify({"error": "No recording ZIP was downloaded. Please ensure there are recent call recordings for this user."}), 404

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

        transcript = transcribe_audio(audio_stream,actual_user_id, filename=os.path.basename(audio_path))

        custom_prompt = request.args.get("prompt", "").strip()
        prompt_to_use = custom_prompt if custom_prompt else ""

        analysis = analyze_text(transcript, default_prompt=prompt_to_use)

        return jsonify({
            "transcription": transcript,
            "analysis": analysis
        })

    except Exception as e:
        print(f"❌ Exception in transcribe_and_analyze: {str(e)}")
        return jsonify({"error": str(e)}), 500


@transcribe_bp.route("/calls", methods=["GET"])
@login_required
def get_call():
    try:
        user_id = current_user.get_actual_id()
        call_infos = get_calls(user_id, 5)

        calls = []
        for info in call_infos:
            tags = {tag['key']: tag['value'] for tag in info.get('tags', [])}
            timestamp_ms = tags.get('endTime')
            timestamp_ms = int(timestamp_ms)
            readable_str = datetime.fromtimestamp(timestamp_ms / 1000).strftime("%Y-%m-%d %H:%M:%S")

            calls.append({
                'userName': tags.get('userName'),
                'direction': tags.get('direction'),
                'left': tags.get('leftChannelEndpointName1'),
                'right': tags.get('rightChannelEndpointName1'),
                'id': info['id'],
                'time': readable_str
            })
        print(calls[0])

        return jsonify(calls=calls)

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@transcribe_bp.route("/transscribespecificcall", methods=["GET"])
@login_required
def transcribe_specific_call():
    try:
        actual_user_id = current_user.get_actual_id()
        call_id = request.args.get("id")
        if not call_id:
            return jsonify({"error": "Missing call ID"}), 400

        print(f"🔐 Transcribing for user actual ID: {actual_user_id}, Call ID: {call_id}")

        zip_path = download_single(actual_user_id, call_id)
        print(f"📦 Downloaded ZIP path: {zip_path}")

        if not zip_path:
            return jsonify({"error": "No recording ZIP was downloaded. Please ensure there are recent call recordings for this user."}), 404

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

        transcript = transcribe_audio(audio_stream,actual_user_id, filename=os.path.basename(audio_path))

        custom_prompt = request.args.get("prompt", "").strip()
        prompt_to_use = custom_prompt if custom_prompt else ""

        analysis = analyze_text(transcript, default_prompt=prompt_to_use)

        return jsonify({
            "transcription": transcript,
            "analysis": analysis
        })

    except Exception as e:
        print(f"❌ Exception in transcribe_and_analyze: {str(e)}")
        return jsonify({"error": str(e)}), 500
