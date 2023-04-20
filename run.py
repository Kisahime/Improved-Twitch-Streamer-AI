import json
import requests
from pydub import AudioSegment
from pydub.playback import play
import io
from twitchio.ext import commands
import creds
import openai

def initVar():
    global EL_key
    global EL_voice
    global EL
    global gpt3_key
    global OAI

    try:
        with open("config.json", "r") as json_file:
            data = json.load(json_file)
    except:
        print("Unable to open JSON file.")
        exit()
        
    class OAI:
        key = data["keys"][0]["OAI_key"]
        model = data["OAI_data"][0]["model"]
        prompt = data["OAI_data"][0]["prompt"]
        temperature = data["OAI_data"][0]["temperature"]
        max_tokens = data["OAI_data"][0]["max_tokens"]
        top_p = data["OAI_data"][0]["top_p"]
        frequency_penalty = data["OAI_data"][0]["frequency_penalty"]
        presence_penalty = data["OAI_data"][0]["presence_penalty"]

    class EL:
        key = data["keys"][0]["EL_key"]
        voice = data["EL_data"][0]["voice"]

    gpt3_key = data["keys"][0]["GPT3_key"]


async def call_api(message, conversation_history):
    openai.api_key = OAI.key
    start_sequence = " #########"
    # Join the conversation history and the new message
    history_str = "\n".join([f"{entry['user']}: {entry['message']}" for entry in conversation_history])
    prompt = f"{OAI.prompt}\n\n{start_sequence}\n{history_str}\n{message}\n{start_sequence}\n"
    response = openai.Completion.create(
        model=OAI.model,
        prompt=prompt,
        temperature=OAI.temperature,
        max_tokens=OAI.max_tokens,
        top_p=OAI.top_p,
        frequency_penalty=OAI.frequency_penalty,
        presence_penalty=OAI.presence_penalty
    )

    json_object = json.loads(str(response))
    return(json_object['choices'][0]['text'])

async def TTS(message):
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{EL.voice}"
    headers = {
        "accept": "audio/mpeg",
        "xi-api-key": EL.key,
        "Content-Type": "application/json",
    }
    data = {
        "text": message,
        "voice_settings": {"stability": 0.75, "similarity_boost": 0.75},
    }

    response = requests.post(url, headers=headers, json=data)
    audio_content = AudioSegment.from_file(io.BytesIO(response.content), format="mp3")
    play(audio_content)


class Bot(commands.Bot):
    def __init__(self):
        # Initialise our Bot with our access token, prefix and a list of channels to join on boot...
        # prefix can be a callable, which returns a list of strings or a string...
        # initial_channels can also be a callable which returns a list of strings...

        super().__init__(
            token=creds.TWITCH_TOKEN, prefix="!", initial_channels=[creds.TWITCH_CHANNEL]
        )
        self.conversation_history = []

    async def event_ready(self):
        # Notify us when everything is ready!
        # We are logged in and ready to chat and use commands...
        print(f"Logged in as | {self.nick}")

    async def event_message(self, message):
        # Ignore messages from a specific user
        if message.author.name.lower() == "okatsu_arisa":
            return
        # Messages with echo set to True are messages sent by the bot...
        # For now we just want to ignore them...
        if message.echo:
            return

        # Append message to the conversation history
        self.conversation_history.append({'user': message.author.name, 'message': message.content})

        # Generate a response based on the conversation history and the new message
        response = await call_api(message.content, self.conversation_history)
        await TTS(response)


if __name__ == "__main__":
    initVar()
    print("\n\Running!\n\n")
    Bot().run()