# AI Interview Bot

A Streamlit web app that simulates a real-time job interview using Google Gemini (Generative AI). The bot acts as an HR executive, asks you interview questions based on your background, and provides actionable feedback at the end.
# Live Demo
[Test the app for yourself](https://interview-app-wn8ecngahukfmkkss57arz.streamlit.app/)


## Features
- Interactive interview simulation with a conversational UI
- Customizable candidate profile (name, experience, skills, role, company)
- 5-turn interview session
- Real-time streaming responses from Gemini
- Automated, structured feedback with rating and improvement tips

## Setup

### 1. Clone the repository
```
git clone <your-repo-url>
cd ai-interview-bot
```

### 2. Install dependencies
```
pip install streamlit google-generativeai
```

### 3. Set up your Google API Key
- For local development, set the environment variable:
  - On Windows (PowerShell):
    ```powershell
    $env:GOOGLE_API_KEY="your-google-api-key"
    ```
  - On macOS/Linux:
    ```bash
    export GOOGLE_API_KEY="your-google-api-key"
    ```
- For Streamlit Cloud, add `GOOGLE_API_KEY` to your `secrets.toml`.

### 4. Run the app
```
streamlit run app.py
```

## Usage
1. Fill in your personal and job details on the setup screen.
2. Click **Start Interview**.
3. Respond to the interview questions (5 turns).
4. After the interview, click **Get Feedback** for a detailed review and tips.
5. Click **Restart Interview** to try again.

## Notes
- Your API key is required for the app to function.
- The app uses the latest Gemini model for both interview and feedback phases.
- No data is stored or sent anywhere except to the Gemini API for processing.

## License
MIT License
