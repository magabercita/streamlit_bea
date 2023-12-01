# token = 'r8_QvazaChl8kIOXHVVpliNR9a6YstIkTj3upafN'

import streamlit as st
import replicate
import os
import requests
from PIL import Image
from io import BytesIO

# App title
st.set_page_config(page_title="Chatbot Bea")

# Replicate Credentials
with st.sidebar:
    st.title('Chatbot Bea')
    if 'REPLICATE_API_TOKEN' in st.secrets:
        st.success('API key already provided!', icon='✅')
        replicate_api = st.secrets['REPLICATE_API_TOKEN']
    else:
        replicate_api = st.text_input('Enter Replicate API token:', type='password')
        if not (replicate_api.startswith('r8_') and len(replicate_api)==40):
            st.warning('Please enter your credentials!', icon='⚠️')
        else:
            st.success('Proceed to entering your prompt message!', icon='👉')
    os.environ['REPLICATE_API_TOKEN'] = replicate_api


    # para darle los parametros al desplegable de la izquierda en el streamlit
    st.subheader('Models and parameters')
    selected_model = st.sidebar.selectbox('Choose a Llama2 model', ['Llama2-7B', 'Llama2-13B', 'Stable-Diffusion'], key='selected_model')
    if selected_model == 'Llama2-7B':
        llm = 'a16z-infra/llama7b-v2-chat:4f0a4744c7295c024a1de15e1a63c880d3da035fa1f49bfd344fe076074c8eea'
    elif selected_model == 'Llama2-13B':
        llm = 'a16z-infra/llama13b-v2-chat:df7690f1994d94e96ad9d568eac121aecf50684a0b0963b25a41cc40061269e5'
    elif selected_model == 'Stable-Diffusion':
        llm = "stability-ai/stable-diffusion:ac732df83cea7fff18b8472768c88ad041fa750ff7682a21affe81863cbe77e4"
    temperature = st.sidebar.slider('temperature', min_value=0.01, max_value=5.0, value=0.1, step=0.01)
    top_p = st.sidebar.slider('top_p', min_value=0.01, max_value=1.0, value=0.9, step=0.01)
    max_length = st.sidebar.slider('max_length', min_value=32, max_value=128, value=120, step=8)
    st.markdown('📖 Learn how to build this app in this [blog](https://blog.streamlit.io/how-to-build-a-llama-2-chatbot/)!')

# Store LLM generated responses
if "messages" not in st.session_state.keys():
    st.session_state.messages = [{"role": "assistant", "content": "How may I assist you today?"}]

# Display or clear chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

def clear_chat_history():
    st.session_state.messages = [{"role": "assistant", "content": "How may I assist you today?"}]
st.sidebar.button('Clear Chat History', on_click=clear_chat_history)

# Function for generating LLaMA2 response. Refactored from https://github.com/a16z-infra/llama2-chatbot
def generate_llama2_response(prompt_input):
    string_dialogue = "You are a helpful assistant. You do not respond as 'User' or pretend to be 'User'. You only respond once as 'Assistant'."
    for dict_message in st.session_state.messages:          # te saca los mensajes del chatbot. usuario eres tu y asistente es el prompt
        if dict_message["role"] == "user":
            string_dialogue += "User: " + dict_message["content"] + "\n\n"
        else:
            string_dialogue += "Assistant: " + dict_message["content"] + "\n\n"

            # este ultimo output es el ultimo mensaje le estamos diciendo el modelo de replicate que estamos llamando. Llama, es de meta y son opensource. aquí en el output está la respuesta que te dará el asistente
    output = replicate.run('a16z-infra/llama13b-v2-chat:df7690f1994d94e96ad9d568eac121aecf50684a0b0963b25a41cc40061269e5', 
                           input={"prompt": f"{string_dialogue} {prompt_input} Assistant: ",
                                  "temperature":temperature, "top_p":top_p, "max_length":max_length, "repetition_penalty":1})
                                    # la temperatura, la palabra que más brilla o palabras que más brillan. puedes tener un rango de temperaturas. repetition penalty para que no te ponga dos veces la misma palabra 
    return output

# User-provided prompt
if prompt := st.chat_input(disabled=not replicate_api):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)


## del notebook 'model_api_calls'
def generate_diff_response(prompt_input):
    output = replicate.run(
        "stability-ai/stable-diffusion:ac732df83cea7fff18b8472768c88ad041fa750ff7682a21affe81863cbe77e4",
        input={"prompt": prompt_input})
        
    return str(output).replace('[','').replace(']','').replace("'","")


# Generate a new response if last message is not from assistant
if st.session_state.messages[-1]["role"] != "assistant":
        if selected_model == 'Stable-Diffusion':
            with st.chat_message("assistant"):
                with st.spinner("Drawing..."):
                    response = generate_diff_response(prompt)
                    # Obtener la imagen de la URL
                    response = requests.get(response)
                    if response.status_code == 200:
                        # Abrir la imagen desde los datos binarios en memoria
                        image = Image.open(BytesIO(response.content))
                        st.image(image) 
                   

        else:
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    response = generate_llama2_response(prompt)
                    placeholder = st.empty()
                    full_response = ''
                    for item in response:
                        full_response += item
                        placeholder.markdown(full_response)
                    placeholder.markdown(full_response)
            message = {"role": "assistant", "content": full_response}
            st.session_state.messages.append(message)

# Generate a new response if last message is not from assistant
# if st.session_state.messages[-1]["role"] != "assistant":
#     with st.chat_message("assistant"):
#         with st.spinner("Thinking..."):
#             response = generate_llama2_response(prompt)
#             placeholder = st.empty()
#             full_response = ''
#             for item in response:
#                 full_response += item
#                 placeholder.markdown(full_response)
#             placeholder.markdown(full_response)
#     message = {"role": "assistant", "content": full_response}
#     st.session_state.messages.append(message)