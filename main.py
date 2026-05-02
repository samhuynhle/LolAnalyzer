import os
import argparse
from dotenv import load_dotenv
from src.analyzer import MatchAnalyzer

def main():
    load_dotenv()
    api_key = os.getenv("RIOT_API_KEY")
    if not api_key:
        print("Error: RIOT_API_KEY not found in .env file.")
        return

    parser = argparse.ArgumentParser(description="Analyze League of Legends player performance.")
    parser.add_argument("name", help="Riot ID Name (e.g., 'Spear Shot')")
    parser.add_argument("tag", help="Riot ID Tag (e.g., '1111')")
    parser.add_argument("--region", help="Region (e.g., EUW1, NA1, KR). Optional: will search if omitted.")
    parser.add_argument("--count", type=int, default=52, help="Number of matches to analyze. Default: 52")
    parser.add_argument("--queue", type=int, help="Queue ID (e.g., 420 for SoloQ, 440 for Flex).")
    
    args = parser.parse_args()
    
    try:
        analyzer = MatchAnalyzer(api_key.strip(), args.name, args.tag, args.region, args.count)
        analyzer.run(queue=args.queue)
    except ValueError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()
