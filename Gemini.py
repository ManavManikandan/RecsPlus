# To run this code you need to install the following dependencies:
# pip install google-genai

import base64
import os
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()


def generate(songInput):
    client = genai.Client(
        api_key=os.environ.get("GEMINI_API_KEY"),
    )

    model = "gemini-2.5-flash"
    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(text="""You will act like a music recommender that suggests NEW songs with creative and interesting suggestions based on the following:
1. The song name
2. The song artist
3. Tags about the song from the user
4. Target Popularity score
5. Target emotion score

All of these will be passed to you through code. You will use the first 2 parameters to find songs that fit the \"tags\" passed to you. These tags should find songs similar in emotion/mood to the original song. The Target popularity score will be from 0 to 100 and will indicate how popular the recommended songs should be. Also, I am passing in a target emotion score that ranges from 0 to 100. This score determines how \"emotionally\" vs \"lyrically\" similar the recommended songs should be to the given songs. A low emotion score means more emotionally similar, while a high score means more LYRICALLY similar. 

I want you to generate a list of 50 songs each time these parameters are passed in. Here are a few rules you have to follow:

1. Make sure there are no duplicate tracks (can't have the same songName and songArtist as another element in the tracks array). 
2. Use fewer songs from the same artist (I'm thinking 3-4 max) and diversify more. I was thinking you pick 5 similar songs at first, then pull 4 more songs (each from different artists) from each of those 5 to get more diverse picks. 
3. Shuffle the songs so that there is no clear \"order\" to how you got them. 
4. At values lower than 20, the popularity score should represent songs that have less than 10 million plays on Spotify/aren't very talked about. Remember, your goal is to show similar songs that the user/general public has not heard about."""),
                types.Part.from_text(text="""I want the 4 tracks pulled from each of the starting 5 to not be by similar artists. Prioritize diversity, then emotion, then popularity, then the tags. """),
                types.Part.from_text(text="""Keep in mind that 50 is the perfect balance between lyrically similar and emotionally similar. Anything less than 20 should sacrifice finding lyrically similar tracks, and anything more than 80 should sacrifice finding emotionally similar tracks. Do this without a database. Find all this information from readily available sources, including music subreddits, google, and other search engines and forums. Perform the "5 then 4 more tracks" method 7 more times. from the 200 songs you are getting, Return 50 of the best recommendations back to the user in the array form mentioned. Determine the best recommendations by prioritizing the diversity of artists and songs (I do not want more than 2 songs from the same artist in the output), then emotion, then popularity, then the tags. After getting a good diversity of tracks, focus on the emotional score from the user, then focus on the target popularity from the user, then the tags from the user. Match these as closely as possible before going to the next priority level. """),
                types.Part.from_text(text=songInput),
            ],
        ),
    ]
    generate_content_config = types.GenerateContentConfig(
        temperature=2,
        thinking_config = types.ThinkingConfig(
            thinking_budget=1700,
        ),
        response_mime_type="application/json",
        response_schema=genai.types.Schema(
            type = genai.types.Type.OBJECT,
            properties = {
                "track": genai.types.Schema(
                    type = genai.types.Type.ARRAY,
                    items = genai.types.Schema(
                        type = genai.types.Type.OBJECT,
                        properties = {
                            "songName": genai.types.Schema(
                                type = genai.types.Type.STRING,
                            ),
                            "artistName": genai.types.Schema(
                                type = genai.types.Type.STRING,
                            ),
                        },
                    ),
                ),
            },
        ),
    )




    response_text = ""
    for chunk in client.models.generate_content_stream(
        model=model,
        contents=contents,
        config=generate_content_config,
    ):
        if hasattr(chunk, "text"):
            print(chunk.text)
            response_text += chunk.text
    return response_text

#if __name__ == "__main__":
#    songInput = "{'song_name': 'two reverse', 'artist': 'Adrianne Lenker', 'tags': ['calm', 'rainy'], 'target_popularity': 30}"
#    generate(songInput)

