import asyncio
from fastmcp import Client
from fastmcp.client.transports import StreamableHttpTransport
from mcp_clinic.auth import make_token

URL = "http://127.0.0.1:8003/mcp"


async def call(role, user_id, tool, args=None):
    t = StreamableHttpTransport(URL, headers={"X-Clinic-Token": make_token(user_id, role)})
    async with Client(t) as c:
        try:
            r = await c.call_tool(tool, args or {})
            return r.data
        except Exception as e:
            return f"ERROR: {e}"


async def main():
    t = StreamableHttpTransport(URL, headers={"X-Clinic-Token": make_token(0, "system")})
    async with Client(t) as c:
        print("Total tools:", len(await c.list_tools()))

    tests = [
        ("user", 1, "my_prescriptions", {"user_id": 1}),
        ("user", 1, "my_bills", {"user_id": 1}),
        ("user", 1, "all_appointments", {}),          # denied hona chahiye
        ("super_admin", 2, "all_appointments", {}),
        ("super_admin", 2, "pending_bills", {}),
        ("user", 1, "system_health", {}),             # denied hona chahiye
        ("system", 0, "system_health", {}),
        ("system", 0, "system_stats", {}),
    ]
    for role, uid, tool, args in tests:
        print(f"\n[{role}] {tool} ->", await call(role, uid, tool, args))


asyncio.run(main())