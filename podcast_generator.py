import os
import re
import sys
from openai import OpenAI
from elevenlabs import ElevenLabs, Voice, VoiceSettings
from PyPDF2 import PdfReader
from ebooklib import epub
from bs4 import BeautifulSoup
import docx
from pydub import AudioSegment
from dotenv import load_dotenv

load_dotenv()

openai_client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))

elevenlabs_client = ElevenLabs(api_key=os.environ.get('ELEVENLABS_API_KEY'))

speaker_voice_map = {
    'Host1': 'CwhRBWXzGAHq8TQ4Fs17',
    'Host2': 'FGY2WhTYpPnrIDTdsKH5'
}

def extract_text_from_pdf(file_path):
    text = ''
    with open(file_path, 'rb') as file:
        pdf_reader = PdfReader(file)
        for page in pdf_reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text
    return text

def extract_text_from_epub(file_path):
    book = epub.read_epub(file_path)
    text = ''
    for item in book.get_items():
        if item.get_type() == epub.ITEM_DOCUMENT:
            soup = BeautifulSoup(item.get_content(), 'html.parser')
            text += soup.get_text()
    return text

def extract_text_from_docx(file_path):
    doc = docx.Document(file_path)
    text = '\n'.join([para.text for para in doc.paragraphs])
    return text

def extract_text_from_txt(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        text = f.read()
    return text

messages = []

def generate_podcast_script(text, format_option='monologue', is_first_chunk=False):
    if is_first_chunk:
        user_prompt = {
            "role": "user",
            "content": f"""- {'The script should be in a monologue format, spoken by \'Host1\'. It should be a smooth, engaging podcast script covering the information in the source text as precisely as can be and is relevant to the key note of the text provided.' if format_option == 'monologue' else 'Create a natural conversation between two hosts named \'Host1\' and \'Host2\'. Alternate lines between the hosts to simulate a dialogue. The lengths of the lines should vary to make the podcast more engaging; for example, Host1 might have longer monologues while Host2 responds briefly.'}
- For **every line**, analyze the mood and expression conveyed by the speech and include annotations indicating the appropriate `stability` and `similarity_boost` settings for speech synthesis, **based on that analysis**.
- **Important:** Every line **must** include both the `stability` and `similarity_boost` annotations.
- **Use only `~:~` as the separator** between elements. Do not use any other separators.
- Open the podcast naturally and do not provide ending statements to the script.
- Do not include titles, music cues, or any text that is not part of the speech.
- No other annotations are to be included that the TTS model will not understand.
- The script should follow **exactly** the format:

  HostName~:~stability=X.X~:~similarity_boost=Y.Y~:~Speech Text

Considerations for stability and similarity_boost:

- **Stability (0.0 to 1.0):** Controls the variability of the speech delivery. Lower values result in more expressive and varied speech, suitable for conveying strong emotions or dynamic expressions. Higher values produce more consistent delivery, appropriate for neutral or serious tones.

- **Similarity Boost (0.0 to 1.0):** Affects how closely the speech matches the original voice. Higher values make the speech sound more like the reference voice, which is useful for maintaining character consistency, while lower values allow for more variation.

**Example with Mood-Based Annotations:**

Host1~:~stability=0.3~:~similarity_boost=0.9~:~Hey there! I'm so excited to share some amazing news with you today!

Host2~:~stability=0.5~:~similarity_boost=0.8~:~That's fantastic! I can't wait to hear all about it.

In the example above:

- **Host1** is expressing excitement, so a lower stability value (e.g., 0.3) allows for more expressive and dynamic speech.

- **Host2** is enthusiastic but slightly more composed, so a moderate stability value (e.g., 0.5) balances expressiveness with consistency.

Text to Convert:


{text}
"""
        }
    elif "STORY ENDS HERE" in text:
        user_prompt = {
            "role": "user",
            "content": f"""- {'The script should be in a monologue format, spoken by \'Host1\'. It should be a smooth, engaging podcast script covering the information in the source text as precisely as can be and is relevant to the key note of the text provided.' if format_option == 'monologue' else 'Create a natural conversation between two hosts named \'Host1\' and \'Host2\'. Alternate lines between the hosts to simulate a dialogue. The lengths of the lines should vary to make the podcast more engaging; for example, Host1 might have longer monologues while Host2 responds briefly.'}
- For **every line**, analyze the mood and expression conveyed by the speech and include annotations indicating the appropriate `stability` and `similarity_boost` settings for speech synthesis, **based on that analysis**.
- **Important:** Every line **must** include both the `stability` and `similarity_boost` annotations.
- **Use only `~:~` as the separator** between elements. Do not use any other separators.
- Continue the conversation naturally, and do not include any opening or closing statements to the podcast script. Do not give any fillers when ending current script, like moving on or diving deeper.
- Do not include titles, openings, music cues, or any text that is not part of the speech.
- No other annotations are to be included that the TTS model will not understand.
- The script should follow **exactly** the format:

  HostName~:~stability=X.X~:~similarity_boost=Y.Y~:~Speech Text

Considerations for stability and similarity_boost:

- **Stability (0.0 to 1.0):** Controls the variability of the speech delivery. Lower values result in more expressive and varied speech, suitable for conveying strong emotions or dynamic expressions. Higher values produce more consistent delivery, appropriate for neutral or serious tones.

- **Similarity Boost (0.0 to 1.0):** Affects how closely the speech matches the original voice. Higher values make the speech sound more like the reference voice, which is useful for maintaining character consistency, while lower values allow for more variation.

**Example with Mood-Based Annotations:**

Host1~:~stability=0.3~:~similarity_boost=0.9~:~Hey there! I'm so excited to share some amazing news with you today!

Host2~:~stability=0.5~:~similarity_boost=0.8~:~That's fantastic! I can't wait to hear all about it.

In the example above:

- **Host1** is expressing excitement, so a lower stability value (e.g., 0.3) allows for more expressive and dynamic speech.

- **Host2** is enthusiastic but slightly more composed, so a moderate stability value (e.g., 0.5) balances expressiveness with consistency.

Text to Convert:


{text}
"""
        }
    else:
        user_prompt = {
            "role": "user",
            "content": f"""- {'The script should be in a monologue format, spoken by \'Host1\'. It should be a smooth, engaging podcast script covering the information in the source text as precisely as can be and is relevant to the key note of the text provided.' if format_option == 'monologue' else 'Create a natural conversation between two hosts named \'Host1\' and \'Host2\'. Alternate lines between the hosts to simulate a dialogue. The lengths of the lines should vary to make the podcast more engaging; for example, Host1 might have longer monologues while Host2 responds briefly.'}
- For **every line**, analyze the mood and expression conveyed by the speech and include annotations indicating the appropriate `stability` and `similarity_boost` settings for speech synthesis, **based on that analysis**.
- **Important:** Every line **must** include both the `stability` and `similarity_boost` annotations.
- **Use only `~:~` as the separator** between elements. Do not use any other separators.
- Continue the conversation naturally, and do not include any opening statements or endings or conclusions  to the podcast script. Do not give any fillers when ending current script, like moving on or diving deeper.
- Do not include titles, openings, closings, music cues, or any text that is not part of the speech.
- No other annotations are to be included that the TTS model will not understand.
- The script should follow **exactly** the format:

  HostName~:~stability=X.X~:~similarity_boost=Y.Y~:~Speech Text

Considerations for stability and similarity_boost:

- **Stability (0.0 to 1.0):** Controls the variability of the speech delivery. Lower values result in more expressive and varied speech, suitable for conveying strong emotions or dynamic expressions. Higher values produce more consistent delivery, appropriate for neutral or serious tones.

- **Similarity Boost (0.0 to 1.0):** Affects how closely the speech matches the original voice. Higher values make the speech sound more like the reference voice, which is useful for maintaining character consistency, while lower values allow for more variation.

**Example with Mood-Based Annotations:**

Host1~:~stability=0.3~:~similarity_boost=0.9~:~Hey there! I'm so excited to share some amazing news with you today!

Host2~:~stability=0.5~:~similarity_boost=0.8~:~That's fantastic! I can't wait to hear all about it.

In the example above:

- **Host1** is expressing excitement, so a lower stability value (e.g., 0.3) allows for more expressive and dynamic speech.

- **Host2** is enthusiastic but slightly more composed, so a moderate stability value (e.g., 0.5) balances expressiveness with consistency.

Text to Convert:


{text}
"""
        }
        
    messages.append(user_prompt)

    response = openai_client.chat.completions.create(
        messages=messages,
        model="gpt-4o-mini",
    )

    script = response.choices[0].message.content.strip()
    print(user_prompt)
    return script


def parse_script(script_text):
    lines = script_text.strip().split('\n')
    script_data = []

    for line_num, line in enumerate(lines):
        if not line.strip():
            continue

        parts = line.split('~:~')

        if len(parts) != 4:
            speaker = parts[0].strip() if len(parts) > 0 else 'Host1'
            stability = 0.5
            similarity_boost = 0.9
            text = parts[-1].strip() if len(parts) > 1 else ''
        else:
            speaker = parts[0].strip()
            try:
                stability_match = re.search(r'stability\s*=\s*([0-9]*\.?[0-9]+)', parts[1].strip(), re.IGNORECASE)
                similarity_match = re.search(r'similarity_boost\s*=\s*([0-9]*\.?[0-9]+)', parts[2].strip(), re.IGNORECASE)
                
                stability = float(stability_match.group(1)) if stability_match else 0.5
                similarity_boost = float(similarity_match.group(1)) if similarity_match else 0.9
            except ValueError as e:
                stability = 0.5
                similarity_boost = 0.9
            text = parts[3].strip()

        script_data.append({
            'speaker': speaker,
            'stability': stability,
            'similarity_boost': similarity_boost,
            'text': text
        })

    return script_data


def synthesize_speech(script_data):
    audio_segments = []
    for idx, line in enumerate(script_data):
        text = line['text']
        if not text:
            continue
        stability = line['stability'] if line['stability'] is not None else 0.75
        similarity_boost = line['similarity_boost'] if line['similarity_boost'] is not None else 0.75
        voice_name_or_id = speaker_voice_map.get(line['speaker'], 'Default')
        audio = elevenlabs_client.generate(
            text=text,
            voice=Voice(voice_id=voice_name_or_id,
                        settings=VoiceSettings(stability=stability, similarity_boost=similarity_boost)),
            model="eleven_multilingual_v2",
        )
        temp_filename = f'temp_audio_{idx}.mp3'
        with open(temp_filename, 'wb') as f:
            for i in audio:
                f.write(i)
        audio_segments.append(temp_filename)

    return audio_segments


def combine_audio_files(audio_segments, output_filename='output_podcast.mp3'):
    combined = AudioSegment.empty()
    for filename in audio_segments:
        segment = AudioSegment.from_file(filename)
        combined += segment + AudioSegment.silent(duration=500)
    combined.export(output_filename, format='mp3')
    return output_filename

def cleanup_temp_files(audio_segments):
    for filename in audio_segments:
        try:
            os.remove(filename)
        except Exception as e:
            print(f"Error deleting file {filename}: {e}")

def chunk_text(text, max_length=4096):
    sentences = re.split('(?<=[.!?]) +', text)
    chunks = []
    current_chunk = ''

    for sentence in sentences:
        if len(current_chunk) + len(sentence) <= max_length:
            current_chunk += sentence + ' '
        else:
            chunks.append(current_chunk.strip())
            current_chunk = sentence + ' '
    if current_chunk:
        chunks.append(current_chunk.strip())
    return chunks

def main(file_path, format_option='monologue', filename='output_podcast.mp3'):
    file_extension = os.path.splitext(file_path)[1].lower()
    if file_extension == '.pdf':
        text = extract_text_from_pdf(file_path)
    elif file_extension == '.epub':
        text = extract_text_from_epub(file_path)
    elif file_extension == '.docx':
        text = extract_text_from_docx(file_path)
    elif file_extension == '.txt':
        text = extract_text_from_txt(file_path)
    else:
        raise ValueError('Unsupported file type')

    if not text:
        raise ValueError('No text extracted from the input file.')

    text += "\nSTORY ENDS HERE"
    text_chunks = chunk_text(text, max_length=4096)

    scripts = []
    for idx, chunk in enumerate(text_chunks):
        is_first_chunk = idx == 0
        script = generate_podcast_script(
            chunk,
            format_option=format_option,
            is_first_chunk=is_first_chunk
        )
        scripts.append(script)

    full_script = '\n'.join(scripts)
    script_data = parse_script(full_script)
    audio_segments = synthesize_speech(script_data)

    if not audio_segments:
        raise ValueError('No audio segments were generated.')

    output_filename = filename.rsplit(".")[0]+".mp3"
    combine_audio_files(audio_segments, output_filename="outputs\\"+output_filename)
    cleanup_temp_files(audio_segments)

    return filename.rsplit(".")[0]+".mp3"#output_filename
    
#if __name__ == "__main__":
#    args = sys.argv[1:]
#    main(args[0],args[2])