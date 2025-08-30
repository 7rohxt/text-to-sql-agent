import streamlit as st
from langchain_helper import final_sql_agent

st.set_page_config(page_title="Rohit's SQL Agent", page_icon="🤖", layout="centered")

st.title("🤖 Rohit's SQL Agent")
st.write("Ask questions in natural language and get instant SQL-powered answers from your T-shirts store database.")

user_query = st.text_input("Enter your question:", placeholder="e.g., How many Adidas T-shirts do I have left in my store?")

if st.button("Get Answer") or user_query:
    if user_query.strip():
        with st.spinner("Generating answer..."):
            try:
                response = final_sql_agent.invoke(user_query)
                if isinstance(response, dict):
                    final_answer = response.get("output", "No output found.")
                else:
                    final_answer = response
                st.success(final_answer)

                with st.expander("Show reasoning (intermediate steps)"):
                    st.write(response)

            except Exception as e:
                st.error(f"Error: {e}")
    else:
        st.warning("Please enter a question.")
