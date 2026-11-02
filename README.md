# Ikigai

**Your mind. Your meaning. Your way.**

An AI-powered mental wellness and self-discovery companion that supports emotional well-being, self-awareness, resilience, and independent decision-making.

## The idea

Ikigai is inspired by *svadharma*: the idea of living by your own nature and path instead of imitating someone else's. Different people need different things on different days, so Ikigai is built around two ways of helping:

- **Support** is for when you want comfort and coping tools right now.
- **Reflect** is for when you want to hear your own voice again. Instead of telling you what to do, it listens, reflects back what matters to you, and asks one open question.

Reflect behavior currently switches on automatically when someone asks the AI to decide for them or leans on it heavily. A manual toggle is planned.

## What it does today

- Streamlit chat app with optional mood survey and mood history
- LangGraph workflow: intent detection, safety checks, and intent-specific generation settings
- Reflective replies for decision-delegation messages: no direct answers, no resource links, one open question
- Fixed, reviewed crisis reply with 988 and Crisis Text Line (741741) that never depends on a model call
- Medical-boundary handling: no diagnosis or medication advice, redirects to professionals
- Prompt-injection and obfuscation defenses
- Optional single resource suggestion, only when it helps
- Automated tests for intent routing and safety cases

## Model setup

The chat model is configurable through environment variables and works with any OpenAI-compatible provider, so it isn't tied to one model that might be retired. See `.env.example`.

## Run it locally

1. Install dependencies:
   `pip install streamlit langchain-core langchain-openai langgraph openai python-dotenv`
2. Copy `.env.example` to `.env` and fill in your own keys. Never commit `.env`.
3. Start the app:
   `streamlit run app.py`
4. Run the tests:
   `python test_intent.py`

## Roadmap

- [x] Reflective handling for over-reliance and decision-delegation
- [x] Hard-coded crisis response
- [ ] Support / Reflect mode toggle in the app
- [ ] End-of-conversation reflection note
- [ ] Broader crisis detection beyond keywords
- [ ] Wind-down behavior as a user finds clarity
- [ ] Fine-tuning experiment on an open model, with a before/after evaluation
- [ ] Public demo link

## Privacy and limits

Ikigai is not a therapist and not a substitute for professional care or crisis services. It is for adults. If you are in crisis, call or text 988 (US) or visit findahelpline.com for other countries. When a hosted model provider is used, messages are sent to that provider under its terms.

## Background

Originally built as a group project for INFO 7375 (Prompt Engineering for Generative AI) at Northeastern University. This version is my independent redesign and extension.
