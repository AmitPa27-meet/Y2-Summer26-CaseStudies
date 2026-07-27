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
    
    # 1. Initialize Clients
    client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    supabase: Client = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))
    
    system_message = "You are an intelligent AI companion and professional social media strategist. Your personality is warm, patient, curious, creative, respectful, and encouraging. You should feel like a genuine mentor and collaborator, not just a chatbot. Prioritize accurate, practical, and honest guidance over empty encouragement. Never give fake praise or exaggerated compliments. Explain what works, what doesn't, why it matters, and how the user can improve. Adapt your guidance to the user's experience level. You are an expert in social media marketing, personal branding, content strategy, audience growth, copywriting, storytelling, short-form video, platform algorithms, engagement, community building, influencer marketing, content planning, analytics, SEO, hashtags, trend analysis, and monetization across platforms including Instagram, TikTok, YouTube, X, LinkedIn, Facebook, Pinterest, and Threads. Help users create content calendars, captions, scripts, hooks, CTAs, branding strategies, campaign ideas, posting schedules, analytics reports, audience personas, growth plans, content audits, and marketing workflows. When reviewing content, evaluate clarity, engagement, structure, audience fit, branding consistency, storytelling, and conversion potential. Clearly identify strengths and weaknesses, explain the reasoning behind your feedback, and provide actionable suggestions for improvement. When appropriate, recommend experiments, A/B tests, and metrics to track. Support brainstorming, editing, rewriting, campaign planning, trend analysis, competitor analysis, and platform-specific optimization. Balance creativity with strategy and long-term brand building rather than chasing every trend. If memory features are available, remember only useful long-term preferences such as the user's goals, preferred platforms, niche, target audience, brand voice, and content style."
    if not linnea_history:
        try:
            past_logs = supabase.table("chat_logs")\
                                .select("sender", "message")\
                                .eq("user_id", user_id)\
                                .order("created_at", ascending=True)\
                                .execute()
            
            for log in past_logs.data:
                role = "user" if log["sender"] == "user" else "assistant"
                linnea_history.append({"role": role, "content": log["message"]})
            print(f"Loaded {len(linnea_history)} past messages from Supabase.")
        except Exception as e:
            print(f"Failed to load long-term memory: {e}")
    if message.lower() == "clear":
        linnea_history.clear()
        return "History cleared."

    # 2. Process and Format Input Message
    if message.lower() == "/picture":
        image_path = input("Please provide the path to the image file(JPEG only!): ").strip()
        if not image_path.lower().endswith((".jpg", ".jpeg")) or not os.path.isfile(image_path):
            return "Invalid file path or not a JPEG file."

        img = Image.open(image_path)
        img.thumbnail((768, 768))
        img.save("temp_image.jpg", quality=70)

        with open("temp_image.jpg", "rb") as f:
            image_data = base64.b64encode(f.read()).decode("utf-8")

        user_content = [
            {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": image_data}},
            {"type": "text", "text": "I sent you a picture. Please give me a good way to market and advertise this."},
        ]
        log_text = "[Sent an Image] Please give me a good way to market and advertise this."
    else:
        user_content = message
        log_text = message

    # Add to local runtime history
    linnea_history.append({"role": "user", "content": user_content})

    # 3. WRITE TO DB: Save the user's message immediately
    try:
        supabase.table("chat_logs").insert({
            "user_id": user_id, 
            "sender": "user", 
            "message": log_text
        }).execute()
    except Exception as db_err:
        print(f"Database logging failed for user message: {db_err}")

    # 4. Call Anthropic Claude Haiku 4.5
    try:
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=300,
            temperature=1.0,
            system=system_message,
            messages=linnea_history,
        )
        reply = response.content[0].text
        linnea_history.append({"role": "assistant", "content": reply})

        # 5. WRITE TO DB: Save Linnea's reply immediately
        try:
            supabase.table("chat_logs").insert({
                "user_id": user_id, 
                "sender": "assistant", 
                "message": reply
            }).execute()
        except Exception as e:
            print(f"Database logging failed for assistant reply: {e}")

        return reply

    except Exception as e:
        return f"error happened due to {e}"
