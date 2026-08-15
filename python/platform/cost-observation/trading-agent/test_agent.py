import asyncio
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from trading_agent.agent import root_agent

async def main():
    print("Sending request to root_agent: 'What is the top gainer on BINANCE 1h timeframe?'")
    try:
        response = await root_agent.run("What is the top gainer on BINANCE 1h timeframe?")
        print("\nResponse:")
        print(response)
        
    except Exception as e:
         print(f"Error invoking agent: {e}")

if __name__ == "__main__":
    asyncio.run(main())
