import pandas as pd
import asyncio
from parser import parse_items

async def main():
    data = await parse_items("Developer")
    df = pd.DataFrame(data)
    df.to_csv("D:/projects/project1/data/results.csv", index=False, encoding='utf-8')


if __name__ == "__main__":
    asyncio.run(main())



