"""Load test: simulates many players who queue for 1v1 and type words.

    python loadtest/bots.py --bots 200

Run the server first (python run.py). Watch live numbers at http://localhost:8000/stats
"""
import argparse
import asyncio
import json
import random
import time

import websockets


async def type_words(ws, words, delay):
    try:
        for word in words:
            await ws.send(json.dumps({"type": "word", "text": word}))
            await asyncio.sleep(delay)
    except websockets.ConnectionClosed:
        pass


async def run_bot(index, url, stats):
    delay = random.uniform(0.15, 0.4)          # every bot types at a different speed
    typer = None
    try:
        async with websockets.connect(f"{url}?name=bot{index}") as ws:
            stats["connected"] += 1
            await ws.send(json.dumps({"type": "queue", "size": 1}))
            async for raw in ws:
                message = json.loads(raw)
                stats["messages"] += 1
                if message["type"] == "match_start":
                    typer = asyncio.create_task(type_words(ws, message["words"], delay))
                elif message["type"] == "match_end":
                    stats["finished"] += 1
                    return
    except Exception:
        stats["errors"] += 1
    finally:
        if typer:
            typer.cancel()


async def main(args):
    stats = dict(connected=0, finished=0, errors=0, messages=0)
    started = time.monotonic()
    tasks = []
    for i in range(args.bots):
        tasks.append(asyncio.create_task(run_bot(i, args.url, stats)))
        await asyncio.sleep(args.ramp)        # connect gradually instead of all at once
    await asyncio.gather(*tasks)
    elapsed = time.monotonic() - started
    print(f"bots={args.bots} connected={stats['connected']} finished={stats['finished']} errors={stats['errors']}")
    print(f"time={elapsed:.1f}s  messages received={stats['messages']}  ({stats['messages'] / elapsed:.0f}/s)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--bots", type=int, default=100, help="number of players (use an even number)")
    parser.add_argument("--url", default="ws://localhost:8000/ws")
    parser.add_argument("--ramp", type=float, default=0.01, help="seconds between connections")
    asyncio.run(main(parser.parse_args()))
