# scripts/check_redis_raw.py
import asyncio
import redis.asyncio as redis


async def main():
    client = redis.Redis(host="localhost", port=6379, socket_timeout=15)
    await client.xadd("test-stream", {"foo": "bar"})
    await client.xgroup_create("test-stream", "test-group", id="0", mkstream=True)

    print("waiting for xreadgroup (BLOCK 2000ms)...")
    result = await client.xreadgroup(
        groupname="test-group",
        consumername="test-consumer",
        streams={"test-stream": ">"},
        block=2000,
    )
    print("result:", result)
    await client.aclose()


if __name__ == "__main__":
    asyncio.run(main())