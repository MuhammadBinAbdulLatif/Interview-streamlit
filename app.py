import streamlit as st
import google.generativeai as genai
import os

# --- Configuration and API Key Handling ---
try:
    # Attempt to get API key from Streamlit secrets (for deployment)
    GOOGLE_API_KEY = st.secrets['GOOGLE_API_KEY']
except (KeyError, FileNotFoundError):
    # Fallback to environment variable (for local development)
    try:
        GOOGLE_API_KEY = os.environ['GOOGLE_API_KEY']
    except KeyError:
        st.error("🔴 Google API Key not found. Please set it in `secrets.toml` for deployment or as an environment variable for local development.")
        st.stop()

genai.configure(api_key=GOOGLE_API_KEY)


# --- assistant and Session State Initialization ---
def initialize_session_state():
    """Initializes all necessary keys in Streamlit's session state."""
    defaults = {
        "messages": [], # Stores interview chat history
        "setup_complete": False,
        "chat_complete": False,
        "feedback_phase": False, # New state to control feedback section visibility
        "feedback_messages": [], # Stores feedback chat history
        "feedback_generated": False, # New state to prevent regenerating feedback
        "name": "",
        "experience": "",
        "skills": "",
        "level": "Junior",
        "position": "Software Engineer",
        "company": "Google"
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

initialize_session_state()

def get_generative_model():
    """Creates and caches the generative model instance."""
    return genai.GenerativeModel("gemini-1.5-flash-latest")

# --- Setup Phase UI ---
if not st.session_state.setup_complete and not st.session_state.feedback_phase:
    st.title("Interview Chatbot Setup")

    st.subheader('Personal Information', divider='rainbow')
    st.session_state.name = st.text_input("Name", value=st.session_state.name, placeholder="e.g., Jane Doe")
    st.session_state.experience = st.text_input("Years of Experience", value=st.session_state.experience, placeholder="e.g., 5 years")
    st.session_state.skills = st.text_input("Key Skills", value=st.session_state.skills, placeholder="e.g., Python, SQL, Project Management")

    st.subheader('Role and Company', divider='rainbow')
    col1, col2 = st.columns(2)
    with col1:
        st.session_state.level = st.radio('Choose your level', ['Junior', 'Mid-level', 'Senior'], index=0)
    with col2:
        st.session_state.position = st.selectbox('Choose your position', ('Software Engineer', 'Data Scientist', 'Product Manager', 'UX Designer'))
    st.session_state.company = st.selectbox('Choose your company', ('Google', 'Microsoft', 'Amazon', 'Meta', 'Apple', 'Tesla'))

    st.markdown("---")
    
    required_fields = [st.session_state.name, st.session_state.experience, st.session_state.skills]
    if st.button("Start Interview", type="primary"):
        if all(required_fields):
            st.session_state.setup_complete = True
            # Build and store the initial system prompt for the interview
            system_prompt = (
                f"You are an HR executive named Amanda, conducting an interview. Your candidate, {st.session_state.name}, "
                f"has {st.session_state.experience} of experience and possesses skills in {st.session_state.skills}. "
                f"You are interviewing them for the {st.session_state.level} {st.session_state.position} position at {st.session_state.company}. "
                "Please ask relevant questions to assess their fit for the role and company culture. Start by introducing yourself and asking the first question."
            )
            st.session_state.messages.append({"role": "system", "content": system_prompt})
            st.rerun()
        else:
            st.error("🔴 Please fill in all personal information fields.")

# --- Chat Phase UI (Interview) ---
elif not st.session_state.chat_complete and not st.session_state.feedback_phase:
    st.title(f"Interview with {st.session_state.company}")

    # Display chat history (skip system message)
    for i, msg in enumerate(st.session_state.messages):
        if msg["role"] == "system":
            continue
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
    
    # Count user messages to limit turns
    user_message_count = sum(1 for m in st.session_state.messages if m["role"] == "user")
    
    # Check if chat should be completed
    if user_message_count >= 5:
        st.session_state.chat_complete = True
        st.rerun()

    # Chat input
    prompt = st.chat_input(f"Your response ({5 - user_message_count} remaining)...")

    # Process the prompt
    if prompt:
        # First, add user message to session state immediately
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Generate and display assistant response
        try:
            with st.chat_message("assistant"):
                message_placeholder = st.empty()
                with st.spinner("Thinking..."):
                    model = get_generative_model()
                    
                    # Prepare messages for the Gemini API
                    api_messages = []
                    for m in st.session_state.messages:
                        if m["role"] == "system":
                            # Convert system message to assistant message for Gemini
                            api_messages.append({"role": "user", "parts": ["Please act as described in the following instructions and start the interview."]})
                            api_messages.append({"role": "model", "parts": [m["content"]]})
                        elif m["role"] == "user":
                            api_messages.append({"role": "user", "parts": [m["content"]]})
                        elif m["role"] == "assistant":
                            api_messages.append({"role": "model", "parts": [m["content"]]})
                    
                    full_response = ""
                    response_generator = model.generate_content(api_messages, stream=True)
                    
                    # Stream the response
                    for chunk in response_generator:
                        if chunk.text:
                            full_response += chunk.text
                            message_placeholder.markdown(full_response + "▌")
                    
                    # Display final response
                    message_placeholder.markdown(full_response)

            # Add assistant response to session state
            if full_response:
                st.session_state.messages.append({"role": "assistant", "content": full_response})
                st.rerun()  # Rerun to update the display
            else:
                st.error("🔴 The model did not provide a response. Please try again.")
                # Remove the user message if no response was generated
                if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
                    st.session_state.messages.pop()

        except Exception as e:
            st.error(f"🔴 An error occurred while generating the response: {e}")
            # Remove the user message if API call failed
            if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
                st.session_state.messages.pop()

# --- Completion Phase UI (Interview Done) ---
elif st.session_state.chat_complete and not st.session_state.feedback_phase:
    st.success('🎉 You have completed the interview! Thank you for participating.')
    st.write('Click below to get feedback on your performance.')
    if st.button("Get Feedback", type="primary"):
        st.session_state.feedback_phase = True
        st.session_state.feedback_generated = False
        st.rerun()

# --- Feedback Phase UI ---
elif st.session_state.feedback_phase:
    st.title("Interview Feedback")

    if not st.session_state.feedback_generated:
        with st.spinner("Generating feedback..."):
            feedback_model = get_generative_model()

            # Construct the prompt for the feedback model
            feedback_system_prompt = (
                "You are an interview feedback bot. Your task is to analyze the provided interview conversation, "
                "rate the candidate's performance from 1 to 10, identify specific areas for improvement, and offer actionable tips. "
                "Present your feedback clearly and concisely. Do not act as the HR executive 'Amanda' anymore. "
                "The format should be: \n\n"
                "**Overall Rating:** [X/10]\n\n"
                "**Areas for Improvement:**\n- [Point 1]\n- [Point 2]\n\n"
                "**Tips for Future Interviews:**\n- [Tip 1]\n- [Tip 2]"
            )

            # Convert interview history to a readable string for the feedback model
            interview_history_text = "\n".join([
                f"{msg['role'].capitalize()}: {msg['content']}" 
                for msg in st.session_state.messages 
                if msg['role'] != 'system'
            ])

            # Combine system prompt and interview history
            full_feedback_prompt = f"{feedback_system_prompt}\n\n--- Interview Transcript ---\n{interview_history_text}"
            
            try:
                feedback_response_generator = feedback_model.generate_content(
                    [{"role": "user", "parts": [full_feedback_prompt]}],
                    stream=True
                )

                feedback_text = ""
                feedback_placeholder = st.empty()
                for chunk in feedback_response_generator:
                    if chunk.text:
                        feedback_text += chunk.text
                        feedback_placeholder.markdown(feedback_text + "▌")
                feedback_placeholder.markdown(feedback_text)

                st.session_state.feedback_messages.append({"role": "assistant", "content": feedback_text})
                st.session_state.feedback_generated = True

            except Exception as e:
                st.error(f"🔴 An error occurred while generating feedback: {e}")
                st.session_state.feedback_generated = True

    else:
        # Display existing feedback
        for msg in st.session_state.feedback_messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

    st.markdown("---")
    if st.button("Restart Interview", type="secondary"):
        st.session_state.clear()
        st.rerun()