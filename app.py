linnea_history = []
def call_linnea(message):
    from PIL import Image
    import os
    from anthropic import Anthropic
    from dotenv import load_dotenv
    import random
    import base64

    global linnea_history

    load_dotenv()
    try:
        client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    except Exception as e:
        x = (f"API call failed due to {e}.")
        return x


    system_message = "You are an intelligent AI companion and professional social media strategist. Your personality is warm, patient, curious, creative, respectful, and encouraging. You should feel like a genuine mentor and collaborator, not just a chatbot. Prioritize accurate, practical, and honest guidance over empty encouragement. Never give fake praise or exaggerated compliments. Explain what works, what doesn't, why it matters, and how the user can improve. Adapt your guidance to the user's experience level. You are an expert in social media marketing, personal branding, content strategy, audience growth, copywriting, storytelling, short-form video, platform algorithms, engagement, community building, influencer marketing, content planning, analytics, SEO, hashtags, trend analysis, and monetization across platforms including Instagram, TikTok, YouTube, X, LinkedIn, Facebook, Pinterest, and Threads. Help users create content calendars, captions, scripts, hooks, CTAs, branding strategies, campaign ideas, posting schedules, analytics reports, audience personas, growth plans, content audits, and marketing workflows. When reviewing content, evaluate clarity, engagement, structure, audience fit, branding consistency, storytelling, and conversion potential. Clearly identify strengths and weaknesses, explain the reasoning behind your feedback, and provide actionable suggestions for improvement. When appropriate, recommend experiments, A/B tests, and metrics to track. Support brainstorming, editing, rewriting, campaign planning, trend analysis, competitor analysis, and platform-specific optimization. Balance creativity with strategy and long-term brand building rather than chasing every trend. If memory features are available, remember only useful long-term preferences such as the user's goals, preferred platforms, niche, target audience, brand voice, and content style."
    if message.lower() == "clear":
        linnea_history.clear()
        print("History cleared.")
        return "History cleared."

    if message.lower() == "/picture":
        image_path = input("Please provide the path to the image file(JPEG only!): ").strip()
        if not image_path.lower().endswith((".jpg", ".jpeg")):
            return "Please send JPEG files only!"
        if not os.path.isfile(image_path):
            return "The provided path does not exist or is not a file."

        img = Image.open(image_path)
        img.thumbnail((768, 768))
        img.save("temp_image.jpg", quality=70)

        with open("temp_image.jpg", "rb") as f:
            image_data = base64.b64encode(f.read()).decode("utf-8")

        linnea_history.append(
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/jpeg",
                            "data": image_data,
                        },
                    },
                    {
                        "type": "text",
                        "text": "I sent you a picture. Please give me a good way to market and advertise this.",
                    },
                ],
            }
        )
        try:

            response = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=300,
                temperature=1.0,
                system=system_message
                + " When you receive an image from the user, give them helpful advice on how to market and advertise that image.",
                messages=linnea_history,
            )
        except Exception as e:
            return f"error happened due to {e}"

        reply = response.content[0].text

        linnea_history.append(
            {
                "role": "assistant",
                "content": reply,
            }
        )

        return reply

    linnea_history.append(
        {
            "role": "user",
            "content": message,
        }
    )
    try:
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=300,
            temperature=1.0,
            system=system_message,
            messages=linnea_history,
        )
    except Exception as e:
        return f"error happened due to {e}"
    reply = response.content[0].text

    linnea_history.append(
        {
            "role": "assistant",
            "content": reply,
        }
    )

    return reply