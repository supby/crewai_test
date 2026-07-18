import os
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

from .crew import ResearchCrew

load_dotenv()

OUTPUT_DIR = Path("output")


def run():
    """Main entry point for the CrewAI project."""
    topic = os.getenv("CREW_TOPIC", "The future of AI agents in software development")

    print(f"Starting crew with topic: {topic}")
    print("-" * 50)

    inputs = {"topic": topic}
    result = ResearchCrew().crew().kickoff(inputs=inputs)

    print("\n" + "=" * 50)
    print("FINAL RESULT:")
    print("=" * 50)
    print(result)

    # Save output to the mounted volume
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = OUTPUT_DIR / f"result_{timestamp}.md"
    output_file.write_text(str(result))
    print(f"\nOutput saved to: {output_file}")

    return result


if __name__ == "__main__":
    run()
