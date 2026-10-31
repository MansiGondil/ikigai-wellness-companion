# Ikigai

**Your mind. Your meaning. Your way.**

An AI-powered mental wellness and self-discovery companion that supports emotional well-being, self-awareness, resilience, and independent decision-making.

> Originally built as a group project for INFO 7375 (Prompt Engineering for Generative AI) at Northeastern University. This version is my independent redesign and extension.

## What it does today

- Chat interface (Streamlit) for venting and getting supportive guidance
- LangGraph workflow: intent detection, safety check, intent-based generation settings
- Fine-tuned GPT-3.5-turbo model for empathetic, boundary-aware responses
- Crisis detection with helpline information
- Prompt-injection defenses and input sanitization
- Optional mood survey and mood history

## Where it's going

Ikigai is being redesigned around one idea: the AI should strengthen a person's own judgment, not replace it.

- [ ] Detect over-reliance and external pressure, and respond by reflecting choices back to the user
- [ ] Graduation behavior: help conversations wind down as the user finds clarity
- [ ] Privacy-preserving "autonomy" view that tracks growth without storing raw conversations

## Run it locally

1. Install dependencies:
   `pip install streamlit langchain-core langchain-openai langgraph openai python-dotenv`
2. Create a `.env` file in the project folder:
   `OPENAI_API_KEY=your_key_here`
3. Start the app:
   `streamlit run app.py`

## Disclaimer

Ikigai is not a therapist and not a substitute for professional care. If you are in crisis, call or text 988 (US).