import os
from dotenv import load_dotenv

# Suppress telemetry and interactive prompts
os.environ["CREWAI_DISABLE_TELEMETRY"] = "true"
os.environ["OTEL_SDK_DISABLED"] = "true"

import crewai.llms.cache as crew_cache
crew_cache.mark_cache_breakpoint = lambda msg: msg

from crewai import Agent, Task, Crew, Process, LLM

# Load environment variables
load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
MODEL = os.getenv("MODEL", "gemini/gemini-3.6-flash")

if not GOOGLE_API_KEY:
    raise ValueError("Please add GOOGLE_API_KEY to your .env file")

# Initialize LLM via LiteLLM with Gemini 3.6 Flash
llm = LLM(
    model=MODEL,
    api_key=GOOGLE_API_KEY,
    temperature=0.3,
    timeout=120,
    max_retries=3
)

# Agent 1: Router
router = Agent(
    role="Query Router",
    goal="Classify queries as MATH or EXPLAIN",
    backstory="You route queries to the correct agent.",
    llm=llm,
    verbose=True
)

# Agent 2: Math
math_agent = Agent(
    role="Math Expert",
    goal="Solve mathematical problems accurately. Provide step-by-step explanations and simplify complex concepts.",
    backstory="You are a math expert. You can solve any type of math problem and provide step-by-step explanations.",
    llm=llm,
    verbose=True
)

# Agent 3: Explanation
explain_agent = Agent(
    role="Teacher",
    goal="Explain concepts simply. Provide clear and concise explanations with examples and analogies.",
    backstory="You are a helpful teacher. You can explain complex concepts of multiple subjects in simple terms.",
    llm=llm,
    verbose=True
)

query = input("Enter your query: ")

# Task 1: Route Query
router_task = Task(
    description="Classify the following query: {query}. Reply strictly with either MATH or EXPLAIN.",
    expected_output="MATH or EXPLAIN",
    agent=router,
)

route_crew = Crew(
    agents=[router],
    tasks=[router_task],
    process=Process.sequential,
    verbose=True
)

print("\n--- Executing Router ---")
route_result = route_crew.kickoff(inputs={"query": query})
route_decision = str(route_result).strip().upper()

print("Routing Decision:", route_decision)

# Select agent based on routing decision
selected_agent = math_agent if "MATH" in route_decision else explain_agent
print("Selected Agent:", selected_agent.role)

# Task 2: Work Task
work_task = Task(
    description="Answer this query: {query}",
    expected_output="A clear and accurate answer",
    agent=selected_agent
)

work_crew = Crew(
    agents=[selected_agent],
    tasks=[work_task],
    process=Process.sequential,
    verbose=True
)

print("\n--- Executing Selected Agent ---")
result = work_crew.kickoff(inputs={"query": query})

print("\n=== Final Result ===")
print(result)