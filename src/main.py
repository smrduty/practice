import pandas as pd
import asyncio
from datetime import datetime
from parser import parse_items
from config import SEARCH_QUERY
from config import RESULTS_PATH

async def main():
    data = await parse_items(SEARCH_QUERY)
    df = pd.DataFrame(data)
    df["parsed_at"] = datetime.now().isoformat()
    df["query"] = SEARCH_QUERY
    df.to_csv(RESULTS_PATH, index=False, encoding='utf-8')
    df.drop_duplicates(subset=["url"], inplace=True)


if __name__ == "__main__":
    asyncio.run(main())



