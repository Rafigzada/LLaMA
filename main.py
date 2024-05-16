import streamlit as st
from hugchat import hugchat
from hugchat.login import Login
import pyttsx3
from threading import Thread
import os
import replicate

# Function to generate LLM response
def generate_response(prompt_input, email, passwd):
    # Hugging Face Login
    sign = Login(email, passwd)
    cookies = sign.login()
    # Create ChatBot
    chatbot = hugchat.ChatBot(cookies=cookies.get_dict())
    return chatbot.chat(prompt_input)

# Function to initialize text-to-speech engine
def init_tts():
    engine = pyttsx3.init()
    engine.setProperty("rate", 150)  # Adjust the speaking rate (words per minute)
    return engine

# Function to speak text using text-to-speech engine
def speak_text(text, engine):
    engine.say(text)
    engine.runAndWait()

def run_tts_async(text, engine):
    thread = Thread(target=speak_text, args=(text, engine))
    thread.start()
    thread.join()  # Wait for the thread to finish

# App title
st.set_page_config(page_title=" Ask 💬")

# Initialize or retrieve existing messages and assistant state in st.session_state
if 'messages' not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "How may I help you?"}]
if 'enable_assistant' not in st.session_state:
    st.session_state.enable_assistant = True  # Initialize enable_assistant attribute

# Initialize the text-to-speech engine
engine = init_tts()

# Hugging Face Credentials
with st.sidebar:
    st.title('ASK 💬')
    if ('EMAIL' in st.secrets) and ('PASS' in st.secrets):
        st.success('HuggingFace Login credentials already provided!', icon='✅')
        hf_email = st.secrets['EMAIL']
        hf_pass = st.secrets['PASS']
    else:
        hf_email = st.text_input('Enter E-mail:', type='password')
        hf_pass = st.text_input('Enter password:', type='password')
        if not (hf_email and hf_pass):
            st.warning('Please enter your credentials!', icon='⚠️')
        else:
            st.success('Proceed to entering your prompt message!', icon='👉')

if st.sidebar.button('Save Chat History as Text'):
    # Specify the file path where you want to save the chat history
    file_path = st.text_input('Enter file path to save chat history:', value='chat_history.txt')
    with open(file_path, 'w', encoding='utf-8') as txt_file:
        # Write chat messages to the text file
        for message in st.session_state.messages:
            txt_file.write(f'{message["role"]}: {message["content"]}\n\n')
    st.success(f'Chat history saved to {file_path}!')

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

st.sidebar.checkbox('Enable Assistant', key='enable_assistant', value=st.session_state.enable_assistant)

# User-provided prompt
if prompt := st.chat_input(disabled=not (hf_email and hf_pass) or not st.session_state.enable_assistant):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

# Additional button to listen to the assistant's response
listen_to_response = st.sidebar.checkbox('Listen to Response')

# Generate a new response if the last message is not from the assistant and the assistant is enabled
if st.session_state.messages[-1]["role"] != "assistant" and st.session_state.enable_assistant:
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = generate_response(prompt, hf_email, hf_pass)
            st.write(response)
            # Add the assistant's response to the session state
            message = {"role": "assistant", "content": response}
            st.session_state.messages.append(message)
            # Speak the assistant's response if the user chooses to listen
            if listen_to_response:

                engine = init_tts()
                run_tts_async(response, engine)

# Clear chat history button
if st.sidebar.button('Clear Chat History'):
    st.session_state.messages = [{"role": "assistant", "content": "How may I help you?"}]

selected_model = st.sidebar.selectbox('Choose a Llama2 model', ['Llama2-7B', 'Llama2-13B'], key='selected_model')
if selected_model == 'Llama2-7B':
    llm = 'a16z-infra/llama7b-v2-chat:4f0a4744c7295c024a1de15e1a63c880d3da035fa1f49bfd344fe076074c8eea'
elif selected_model == 'Llama2-13B':
    llm = 'a16z-infra/llama13b-v2-chat:df7690f1994d94e96ad9d568eac121aecf50684a0b0963b25a41cc40061269e5'

def generate_llama2_response(prompt_input):
    string_dialogue = "You are a helpful assistant. You do not respond as 'User' or pretend to be 'User'. You only respond once as 'Assistant'."
    for dict_message in st.session_state.messages:
        if dict_message["role"] == "user":
            string_dialogue += "User: " + dict_message["content"] + "\n\n"
        else:
            string_dialogue += "Assistant: " + dict_message["content"] + "\n\n"
    output = replicate.run(
        'a16z-infra/llama13b-v2-chat:df7690f1994d94e96ad9d568eac121aecf50684a0b0963b25a41cc40061269e5',
        input={"prompt": f"{string_dialogue} {prompt_input} Assistant: "})
    return output


