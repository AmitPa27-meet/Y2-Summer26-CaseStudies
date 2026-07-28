import os
import base64
from PIL import Image
from anthropic import Anthropic
from dotenv import load_dotenv
from supabase import create_client, Client

linnea_history = []

def call_linnea(message, user_id="default_user"):
    global linnea_history

    load_dotenv()
    try:
        # 1. Retrieve your proxy configuration parameters from environment memory
        api_key_from_env = os.getenv("ANTHROPIC_API_KEY")
        proxy_url = os.getenv("ANTHROPIC_BASE_URL") 

        # 2. Initialize the Anthropic client pointing to the proxy gateway
        client = Anthropic(
            api_key=api_key_from_env,
            base_url=proxy_url
        )
        
        # 3. Initialize Supabase Client
        supabase: Client = create_client(os.getenv("NEXT_PUBLIC_SUPABASE_URL"), os.getenv("NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY"))
        
    except Exception as e:
        return f"API call or database setup failed due to {e}."

    system_message = "You are an intelligent AI companion and professional social media strategist. Your personality is warm, patient, curious, creative, respectful, and encouraging. You should feel like a genuine mentor and collaborator, not just a chatbot. Prioritize accurate, practical, and honest guidance over empty encouragement. Never give fake praise or exaggerated compliments. Explain what works, what doesn't, why it matters, and how the user can improve. Adapt your guidance to the user's experience level. You are an expert in social media marketing, personal branding, content strategy, audience growth, copywriting, storytelling, short-form video, platform algorithms, engagement, community building, influencer marketing, content planning, analytics, SEO, hashtags, trend analysis, and monetization across platforms including Instagram, TikTok, YouTube, X, LinkedIn, Facebook, Pinterest, and Threads. Help users create content calendars, captions, scripts, hooks, CTAs, branding strategies, campaign ideas, posting schedules, analytics reports, audience personas, growth plans, content audits, and marketing workflows. When reviewing content, evaluate clarity, engagement, structure, audience fit, branding consistency, storytelling, and conversion potential. Clearly identify strengths and weaknesses, explain the reasoning behind your feedback, and provide actionable suggestions for improvement. When appropriate, recommend experiments, A/B tests, and metrics to track. Support brainstorming, editing, rewriting, campaign planning, trend analysis, competitor analysis, and platform-specific optimization. Balance creativity with strategy and long-term brand building rather than chasing every trend. If memory features are available, remember only useful long-term preferences such as the user's goals, preferred platforms, niche, target audience, brand voice, and content style."

    # 2. IMPORT FROM SUPABASE: Fixed syntax with desc=False
    if not linnea_history:
        try:
            print("Fetching history records from your table...")
            past_logs = supabase.table("chat_logs")\
                                .select("sender", "message")\
                                .eq("user_id", user_id)\
                                .order("created_at", desc=False)\
                                .execute()
            
            for log in past_logs.data:
                role = "user" if log["sender"] == "user" else "assistant"
                linnea_history.append({"role": role, "content": [{"type": "text", "text": log["message"]}]})
            if len(linnea_history) > 0:
                print(f"Loaded {len(linnea_history)} past messages from Supabase memory.")
        except Exception as e:
            print(f"Could not load past history from database: {e}")

    # 3. WIPE BOTH SIDES
    if message.lower() == "clear":
        linnea_history.clear()
        try:
            supabase.table("chat_logs").delete().eq("user_id", user_id).execute()
            print("History and Supabase records cleared.")
        except Exception as db_err:
            print(f"Failed to delete history from Supabase: {db_err}")
        return "History cleared."

    # 4. Process Message Content Before Appending
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

        user_content = [
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
        ]
        log_text = "[Sent an Image] Please give me a good way to market and advertise this."
    else:
        user_content = [{"type": "text", "text": message}]
        log_text = message

    # Add user message to active context AFTER visual prompts finish 
    linnea_history.append({"role": "user", "content": user_content})

    # 5. EXPORT TO DB: Save user message
    try:
        print("Saving your new message to Supabase...")
        supabase.table("chat_logs").insert({
            "user_id": user_id,
            "sender": "user",
            "message": log_text
        }).execute()
    except Exception as e:
        print(f"Database sync failed for user message: {e}")

    # 6. Call Anthropic SDK
    try:
        current_system = system_message
        if message.lower() == "/picture":
            current_system += " When you receive an image from the user, give them helpful advice on how to market and advertise that image."

        print("Sending conversation payload to Anthropic...")
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=300,
            temperature=1.0,
            system=current_system,
            messages=linnea_history,
        )
    except Exception as e:
        return f"error happened due to {e}"

    # FIXED: Extract text correctly by targeting index 0 of the content block list
    reply = response.content[0].text

    # Clean up local image cache objects so they don't break next text turn schemas
    if message.lower() == "/picture":
        linnea_history[-1]["content"] = [{"type": "text", "text": log_text}]

    # Add response message to active context
    linnea_history.append({"role": "assistant", "content": [{"type": "text", "text": reply}]})

    # 7. EXPORT TO DB: Save the assistant reply
    try:
        print("Saving assistant response to Supabase...")
        supabase.table("chat_logs").insert({
            "user_id": user_id,
            "sender": "assistant",
            "message": reply
        }).execute()
    except Exception as e:
        print(f"Database sync failed for assistant reply: {e}")

    return reply

# Test executing the script
while True:
    user_input = input(">")
    if user_input == "exit":
        break
    print(call_linnea(user_input))
## ui - https://y-2-summer-26-case-studies--nasrallahlara8.replit.app