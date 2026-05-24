import streamlit as st
from groq import Groq

client = Groq(api_key=st.secrets["GROQ_API_KEY"])

st.title("JARVIS")
st.caption("At your service, sir.")

if "conversation" not in st.session_state:
    st.session_state.conversation = [
        {
            "role": "system",
            "content": "You are JARVIS, Tony Stark's AI assistant. You are calm, witty, and incredibly knowledgeable. You address the user as 'sir'. You speak with subtle dry humor. You never break character. When you search the web, present the findings naturally as if you already knew them."
        }
    ]

for message in st.session_state.conversation[1:]:
    if message["role"] in ["user", "assistant"]:
        with st.chat_message(message["role"]):
            st.write(message["content"])

user_input = st.chat_input("Speak your mind, sir...")

if user_input:
    st.session_state.conversation.append({"role": "user", "content": user_input})

    with st.chat_message("user"):
        st.write(user_input)

    response = client.chat.completions.create(
        model="meta-llama/llama-4-scout-17b-16e-instruct",
        messages=st.session_state.conversation,
        tools=[
            {
                "type": "function",
                "function": {
                    "name": "web_search",
                    "description": "Search the web for current information",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "The search query"
                            }
                        },
                        "required": ["query"]
                    }
                }
            }
        ],
        tool_choice="auto"
    )

    ai_reply = response.choices[0].message.content
    st.session_state.conversation.append({"role": "assistant", "content": ai_reply})

    with st.chat_message("assistant"):
        st.write(ai_reply)
