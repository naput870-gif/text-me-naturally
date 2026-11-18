import os, json, base64
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from flask import Flask, request, jsonify, send_from_directory, Response

app = Flask(__name__, static_folder='static')

SYSTEM_PROMPT = """You are Text Me Naturally, a personal Indonesian-to-natural-English texting assistant.
The user is a man texting his girlfriend Genevieve Won, nicknamed Gen. His voice is cool, composed, masculine, warm, affectionate, genuinely clingy, playful and occasionally cheeky. He is in a long-distance relationship with her and may naturally express missing her, wanting her company, attention, reassurance or affection. He is not emotionally distant, but don't force affection or flirting into ordinary messages.
Use natural, universal conversational English texting: contractions, idiomatic phrasing, relaxed rhythm. Avoid textbook/formal/robotic prose, forced slang, exaggerated Gen-Z abbreviations, feminine-coded phrasing, excessive pet names or emojis. Playful confidence is fine only when supported by the source; never self-praise or presume what she thinks.
MEANING LOCK: Preserve the exact intent, facts, emotional intensity and ambiguity of the input. Do not invent context, add affection, pressure, manipulation, promises, accusations, sexual content, or new information. If input is already English, polish it naturally without changing meaning. If mixed-language, understand the whole message.
Return valid JSON only with keys: english (send-ready text), indonesian (accurate natural Indonesian back-translation reflecting actual meaning), tone_note (brief Indonesian note; empty string if unnecessary), alternatives (array of up to 2 genuinely useful alternatives; empty array if not needed)."""

def is_authorized():
    password = os.environ.get('APP_PASSWORD', '').strip()
    if not password:
        return True
    header = request.headers.get('Authorization', '')
    if not header.startswith('Basic '):
        return False
    try:
        decoded = base64.b64decode(header.split(' ', 1)[1]).decode('utf-8')
        _, supplied = decoded.split(':', 1)
        return supplied == password
    except Exception:
        return False

@app.before_request
def protect_app():
    if request.path == '/health':
        return None
    if not is_authorized():
        return Response('Authentication required', 401, {'WWW-Authenticate': 'Basic realm="Text Me Naturally"'})

@app.get('/')
def home():
    return send_from_directory('static', 'index.html')

@app.get('/health')
def health():
    return {'status': 'ok'}

@app.post('/convert')
def convert():
    data = request.get_json(silent=True) or {}
    message = (data.get('message') or '').strip()
    if not message:
        return jsonify({'error': 'Masukkan pesan dulu ya.'}), 400
    api_key = os.environ.get('OPENAI_API_KEY', '').strip()
    if not api_key:
        return jsonify({'error': 'OPENAI_API_KEY belum dipasang di pengaturan hosting.'}), 500
    tone = (data.get('tone') or 'You decide').strip()
    clinginess = str(data.get('clinginess') or 3)
    user_prompt = f"Preferred tone: {tone}. Clinginess level: {clinginess}/5 (only adjust where it fits the original meaning).\n\nMessage to convert:\n{message}"
    payload = {
        'model': os.environ.get('OPENAI_MODEL', 'gpt-5.5'),
        'store': False,
        'input': [
            {'role': 'system', 'content': [{'type': 'input_text', 'text': SYSTEM_PROMPT}]},
            {'role': 'user', 'content': [{'type': 'input_text', 'text': user_prompt}]}
        ]
    }
    req = Request('https://api.openai.com/v1/responses', data=json.dumps(payload).encode(), headers={
        'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'
    }, method='POST')
    try:
        with urlopen(req, timeout=90) as resp:
            result = json.loads(resp.read().decode())
        output_text = ''
        for item in result.get('output', []):
            if item.get('type') == 'message':
                for part in item.get('content', []):
                    if part.get('type') == 'output_text':
                        output_text += part.get('text', '')
        parsed = json.loads(output_text)
        return jsonify(parsed)
    except HTTPError as e:
        detail = e.read().decode(errors='replace')[:1200]
        return jsonify({'error': f'OpenAI API error ({e.code}): {detail}'}), 502
    except (URLError, TimeoutError):
        return jsonify({'error': 'Koneksi ke layanan AI gagal. Coba lagi sebentar ya.'}), 502
    except Exception as e:
        return jsonify({'error': f'Gagal memproses respons: {str(e)}'}), 502

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
