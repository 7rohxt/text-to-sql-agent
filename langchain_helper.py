import os
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate, FewShotPromptTemplate
from langchain_community.utilities import SQLDatabase
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.prompts.example_selector import SemanticSimilarityExampleSelector
from langchain.agents import AgentType
from langchain_community.agent_toolkits import create_sql_agent 
from dotenv import load_dotenv

load_dotenv()

from few_shots import few_shots
api_key = os.getenv("OPENAI_API_KEY")
llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0)

db_user = "root"
db_password = "root"
db_host = "localhost"
db_name = "tshirts"

db = SQLDatabase.from_uri(
    f"mysql+pymysql://{db_user}:{db_password}@{db_host}/{db_name}",
    sample_rows_in_table_info=3
)

embeddings = HuggingFaceEmbeddings(model_name='sentence-transformers/all-MiniLM-L6-v2')

texts = [d["Question"] for d in few_shots]

metadatas = [
    {
        "Question": d["Question"],
        "SQLQuery": d["SQLQuery"], 
        "SQLResult": d["SQLResult"], 
        "Answer": d["Answer"]        
    }
    for d in few_shots
]

vectorstore = Chroma.from_texts(
    texts=texts,
    embedding=embeddings,
    metadatas=metadatas
)

example_selector = SemanticSimilarityExampleSelector(
    vectorstore=vectorstore,
    k=2  
)

example_prompt = PromptTemplate(
    input_variables=["Question", "SQLQuery", "SQLResult", "Answer"],  # Fixed variable names
    template="""Question: {Question}
SQLQuery: {SQLQuery}
SQLResult: {SQLResult}
Answer: {Answer}"""
)

few_shot_prompt = FewShotPromptTemplate(
    example_selector=example_selector,
    example_prompt=example_prompt,
    suffix="Question: {input}\nSQLQuery:",
    input_variables=["input"]
)

final_prompt = few_shot_prompt.format(input="How many Adidas T shirts I have left in my store?")
print(final_prompt)

few_shot_examples_str = few_shot_prompt.format(input="{input}")

mysql_instructions = """
You are a MySQL expert. Given an input question, first create a syntactically correct MySQL query to run,
then look at the results of the query and return the answer to the input question.
Unless the user specifies a specific number of examples to obtain, query for at most 5 results using LIMIT.
Never SELECT *; only select needed columns, and wrap column names in backticks (`).
Use only columns that exist; pay attention to which column is in which table.
Use CURDATE() for "today" queries. Be precise and concise.
"""

custom_sql_prompt = PromptTemplate(
    input_variables=["input", "tools", "tool_names", "agent_scratchpad"],
    template=f"""
{mysql_instructions}

# Worked Examples 
{few_shot_examples_str}

You can use the following tools:
{{tools}}

You may call only these tool names:
{{tool_names}}

Use this exact format:
Question: the input question to answer
Thought: think step-by-step about what to do next
Action: one of [{{tool_names}}]
Action Input: the input for the action
Observation: the result of the action
... (you can repeat Thought/Action/Action Input/Observation as needed)
Thought: I now know the final answer
Final Answer: the final answer to the original question

Begin!

Question: {{input}}
{{agent_scratchpad}}

Database schema:
{db.table_info}
"""
)

final_sql_agent = create_sql_agent(
    llm=llm,
    db=db,
    agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    handle_parsing_errors=True,
    prompt=custom_sql_prompt,
    agent_executor_kwargs={"return_intermediate_steps": True},
)

if __name__ == "__main__":
    try:
        result = final_sql_agent.invoke("How many Adidas T-shirts do I have left in my store?")
        print("Result:", result)
    except Exception as e:
        print(f"Error: {e}")