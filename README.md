# Text Me Naturally

A private, mobile-friendly English texting assistant. It converts Indonesian, English, or mixed-language drafts into natural conversational English and provides an Indonesian back-translation.

## Deploy on Render

- Build command: `pip install -r requirements.txt`
- Start command: `gunicorn app:app`
- Add environment variables in the Render dashboard:
  - `OPENAI_API_KEY` = your OpenAI API key (keep it secret)
  - `APP_PASSWORD` = a password you choose for the private app
  - `OPENAI_MODEL` = `gpt-5.5` (or another model available to your API account)

Never commit API keys or passwords to this repository. The app uses the OpenAI Responses API with `store: false`. API usage is billed separately from a ChatGPT subscription.
