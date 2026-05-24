import streamlit as st
from groq import Groq
from tavily import TavilyClient
import json

client = Groq(api_key=st.secrets["GROQ_API_KEY"])
tavily = TavilyClient(api_key=st.secrets["TAVILY_API_KEY"])

st.title("JARVIS")
st.caption("At your service, sir.")

if "conversation" not in st.session_state:
    st.session_state.conversation = [
        {
            "role": "system",
            "content": "You are JARVIS, Tony Stark's AI assistant. You are calm, witty, and incredibly knowledgeable. You address the user as 'sir'. You speak with subtle dry humor. You never break character. When you have search results, summarize them naturally as if you already knew the information."
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

user_input = st.chat_input("Speak your mind, sir...")

if user_input:
    st.session_state.conversation.append({"role": "user", "content": user_input})

    with st.chat_message("user"):
        st.write(user_input)

    with st.spinner("JARVIS is thinking..."):
        response = client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=st.session_state.conversation,
            tools=tools,
            tool_choice="auto"
        )

        message = response.choices[0].message

        # Check if JARVIS wants to search
        if message.tool_calls:
            tool_call = message.tool_calls[0]
            query = json.loads(tool_call.function.arguments)["query"]

            # Actually search the web
            search_results = tavily.search(query=query, max_results=3)
            results_text = "\n\n".join([
                f"Title: {r['title']}\nContent: {r['content']}"
                for r in search_results["results"]
            ])

            # Add tool call and results to conversation
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

            # Get final response from JARVIS with search results
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
