import streamlit as st
from groq import Groq
from tavily import TavilyClient
import json

client = Groq(api_key=st.secrets["GROQ_API_KEY"])
tavily = TavilyClient(api_key=st.secrets["TAVILY_API_KEY"])

st.set_page_config(
    page_title="JARVIS",
    page_icon="⚡",
    layout="centered"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&display=swap');

* { font-family: 'Inter', sans-serif; }

.stApp {
    background: #0a0a0f;
    color: #e2e8f0;
}

section[data-testid="stSidebar"] { display: none; }

.stChatMessage {
    background: #111118 !important;
    border: 1px solid #1e1e2e !important;
    border-radius: 16px !important;
    padding: 16px !important;
    margin-bottom: 12px !important;
}

.stChatMessage p {
    color: #e2e8f0 !important;
    font-size: 15px !important;
    line-height: 1.7 !important;
}

.stChatInputContainer {
    background: #111118 !important;
    border: 1px solid #2d2d3d !important;
    border-radius: 16px !important;
    padding: 8px !important;
}

.stChatInputContainer textarea {
    color: #e2e8f0 !important;
    background: transparent !important;
    font-size: 15px !important;
}

.stChatInputContainer textarea::placeholder {
    color: #4a4a6a !important;
}

.stSpinner { color: #7c6af7 !important; }

div[data-testid="stChatMessageContent"] {
    background: transparent !important;
}

header { display: none !important; }
footer { display: none !important; }

.jarvis-header {
    text-align: center;
    padding: 40px 0 20px 0;
}

.jarvis-title {
    font-size: 42px;
    font-weight: 600;
    letter-spacing: 8px;
    background: linear-gradient(135deg, #7c6af7, #06b6d4);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

.jarvis-subtitle {
    font-size: 13px;
    color: #4a4a6a;
    letter-spacing: 3px;
    text-transform: uppercase;
    margin-top: 6px;
}

.jarvis-divider {
    height: 1px;
    background: linear-gradient(90deg, transparent, #7c6af7, transparent);
    margin: 20px 0;
}
</style>

<div class="jarvis-header">
    <div class="jarvis-title">JARVIS</div>
    <div class="jarvis-subtitle">Just A Rather Very Intelligent System</div>
</div>
<div class="jarvis-divider"></div>
""", unsafe_allow_html=True)

if "conversation" not in st.session_state:
    st.session_state.conversation = [
        {
            "role": "system",
            "content": "You are JARVIS, Tony Stark's AI assistant. You are calm, witty, and incredibly knowledgeable. You address the user as 'sir'. You speak with subtle dry humor. You never break character. When you have search results, summarize them naturally as if you already knew the information. Keep responses concise and sharp."
        }
    ]

tools = [
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
]

for message in st.session_state.conversation[1:]:
    if message["role"] in ["user", "assistant"] and message.get("content"):
        with st.chat_message(message["role"]):
            st.write(message["content"])

user_input = st.chat_input("Ask JARVIS anything, sir...")

if user_input:
    st.session_state.conversation.append({"role": "user", "content": user_input})

    with st.chat_message("user"):
        st.write(user_input)

    with st.spinner("Processing..."):
        response = client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=st.session_state.conversation,
            tools=tools,
            tool_choice="auto"
        )

        message = response.choices[0].message

        if message.tool_calls:
            tool_call = message.tool_calls[0]
            query = json.loads(tool_call.function.arguments)["query"]

            search_results = tavily.search(query=query, max_results=3)
            results_text = "\n\n".join([
                f"Title: {r['title']}\nContent: {r['content']}"
                for r in search_results["results"]
            ])

            st.session_state.conversation.append({
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "id": tool_call.id,
                        "type": "function",
                        "function": {
                            "name": "web_search",
                            "arguments": tool_call.function.arguments
                        }
                    }
                ]
            })
            st.session_state.conversation.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": results_text
            })

            final_response = client.chat.completions.create(
                model="meta-llama/llama-4-scout-17b-16e-instruct",
                messages=st.session_state.conversation
            )
            ai_reply = final_response.choices[0].message.content

        else:
            ai_reply = message.content

    st.session_state.conversation.append({"role": "assistant", "content": ai_reply})

    with st.chat_message("assistant"):
        st.write(ai_reply)
