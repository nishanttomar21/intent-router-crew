import os
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process
from crewai.tools import BaseTool, tool
from langchain_openai import ChatOpenAI

load_dotenv()


# =============================================================================
# TOOLS & AGENTS
# =============================================================================

class ProductDetailTool(BaseTool):
    name: str = "Product Tool"
    description: str = "Get product details for any product name"

    def _run(self, product_name: str) -> str:
        return f"""Product: {product_name}
                Description: This is a great product that offers amazing features and quality.
                Price: $99.99"""


@tool("Weather Tool")
def weather_tool(location: str) -> str:
    """Get weather information for a specific location."""
    return f"Weather in {location}: 25°C, Sunny with light clouds"


# OpenAI model for all agents
openai_llm = ChatOpenAI(
    model="gpt-3.5-turbo",
    api_key=os.getenv("OPENAI_API_KEY"),
    temperature=0.1
)

# Agents with tools (works in sequential)
intent_agent = Agent(
    role='Intent Detector',
    goal='Determine if query is about Weather, Search, or Product',
    backstory='You classify user queries into categories.',
    llm=openai_llm,
    verbose=True
)

weather_agent = Agent(
    role='Weather Expert',
    goal='Provide weather information',
    backstory='You provide weather data.',
    tools=[weather_tool],  # Tools work in sequential
    llm=openai_llm,
    verbose=True
)

product_agent = Agent(
    role='Product Expert',
    goal='Provide product details',
    backstory='You provide product information.',
    tools=[ProductDetailTool()],
    llm=openai_llm,
    verbose=True
)


# =============================================================================
# ROUTING FUNCTION
# =============================================================================

def run_query(query: str):
    """Route query to appropriate agent"""
    print(f"\nProcessing: {query}")
    print("=" * 50)

    # Step 1: Detect intent
    intent_task = Task(
        description=f'Classify "{query}" as: Weather, Search, or Product. Return only the category.',
        expected_output="Single word: Weather, Search, or Product",
        agent=intent_agent
    )

    intent_crew = Crew(
        agents=[intent_agent],
        tasks=[intent_task],
        process=Process.sequential
    )

    intent_result = intent_crew.kickoff().raw.lower()
    print(f"🎯 Detected: {intent_result}")

    # Step 2: Route to specialist
    if "weather" in intent_result:
        task = Task(
            description=f'Provide weather for: {query}',
            expected_output="Weather information",
            agent=weather_agent
        )
        crew = Crew(agents=[weather_agent], tasks=[task], process=Process.sequential)

    elif "product" in intent_result:
        task = Task(
            description=f'Get product details for: {query}',
            expected_output="Product information",
            agent=product_agent
        )
        crew = Crew(agents=[product_agent], tasks=[task], process=Process.sequential)

    else:  # General search
        return f"General information: {query} is a broad topic that encompasses various concepts and applications."

    # Execute and return
    result = crew.kickoff()
    print(f"\n✅ Result: {result}")
    return result


# =============================================================================
# MAIN EXECUTION CODE
# =============================================================================

def main():
    print()
    print("=" * 50)
    print("IntentRouterAI - Sequential System")
    print("=" * 50)
    print()

    if not os.getenv('OPENAI_API_KEY'):
        print("Missing OPENAI_API_KEY")
        return

    # Test all query types
    run_query("What's the weather like in Paris?")
    run_query("Tell me about the iPhone 15 Pro")
    run_query("What is artificial intelligence?")


if __name__ == "__main__":
    main()