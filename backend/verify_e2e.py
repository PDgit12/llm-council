import asyncio
import httpx
import time
import uuid
import sys
import json

API_BASE = "http://localhost:8001"
# Mock user ID for local verification if bypass is enabled, 
# otherwise we need a real token.
MOCK_TOKEN = "TEST_TOKEN_ADMIN" 

async def test_performance():
    print("🚀 Starting Industry-Level E2E Performance Check...")
    
    headers = {
        "Authorization": f"Bearer {MOCK_TOKEN}",
        "Content-Type": "application/json"
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # 1. List Conversations
        start = time.time()
        resp = await client.get(f"{API_BASE}/api/conversations", headers=headers)
        list_latency = (time.time() - start) * 1000
        print(f"✅ List Conversations: {resp.status_code} ({list_latency:.2f}ms)")
        
        # 2. Create Conversation (Optimistic UI Target: < 300ms)
        start = time.time()
        resp = await client.post(
            f"{API_BASE}/api/conversations", 
            headers=headers,
            json={"title": "E2E Test Thread"}
        )
        create_latency = (time.time() - start) * 1000
        conv_id = resp.json().get("id")
        print(f"✅ Create Conversation: {resp.status_code} ({create_latency:.2f}ms)")
        if create_latency > 500:
            print("⚠️ WARNING: Creation latency exceeds industry target (500ms)")
            
        # 3. Message Streaming (TTFR - Time to First Response)
        print("💬 Sending Complex Message & Measuring Partial Event Performance...")
        ttfr = None
        partial_events = 0
        is_complete = False
        start = time.time()
        payload = {
            "content": (
                "HI CAN U HELP ME WITH A CHEAT SHEET FOR CS182 PURDUE UNIVERSITY DISCRETE MATHEMATICS "
                "I HAVE QUIZ TODAY I DON'T KNOW ANYTHING ABOUT IT AND IN THE QUIZ I HAVE SETS, "
                "RELATION FUNCTIONS , PROOF TECHNIQUES , SEQUENCE AND SUMMATIONS , LOGIC FUNDAMENTALS . "
                "I want to score 100/100 in the quiz help me do that"
            )
        }
        
        async with client.stream(
            "POST", 
            f"{API_BASE}/api/conversations/{conv_id}/message/stream",
            headers=headers,
            json=payload
        ) as response:
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    try:
                        event = json.loads(line[6:])
                        evt_type = event.get("type")
                        if ttfr is None:
                            ttfr = (time.time() - start) * 1000
                            print(f"✅ Time to First Response (TTFR): {ttfr:.2f}ms")
                        
                        print(f"  [Event] {evt_type}")
                        
                        if evt_type == "model_activity":
                            model = event.get("data", {}).get("model", "unknown")
                            status = event.get("data", {}).get("status", "unknown")
                            print(f"    📡 Agent Activity: {model} -> {status}")
                            partial_events += 1
                        
                        if evt_type == "stage1_partial":
                            print(f"    ✅ Partial Result Received: {list(event.get('data', {}).keys())[0]}")
                        
                        if evt_type == "error":
                            print(f"❌ STREAM ERROR: {event.get('message')}")
                        
                        if evt_type == "council_complete":
                            print("🚀 Pipeline complete.")
                            is_complete = True
                            break
                    except Exception as e:
                        continue
        
        # 4. Clean up
        await client.delete(f"{API_BASE}/api/conversations/{conv_id}", headers=headers)

    print("\n--- PERFORMANCE REPORT ---")
    if ttfr is not None:
        print(f"Stream Start Latency: {ttfr:.2f}ms")
    else:
        print("Stream Start Latency: N/A (No response received)")
    print(f"Partial Events during Exploration: {partial_events}")
    print("--------------------------")
    
    if partial_events >= 4 and ttfr < 3000:
        print(f"🌟 RESULT: PASS (Incremental Feedback Verified with {partial_events} agents)")
    else:
        print(f"❌ RESULT: FAIL (Blocking Behavior or insufficient agents detected: {partial_events})")
    
    if create_latency < 500 and ttfr < 3000:
        print("🌟 RESULT: PASS (Industry Grade)")
    else:
        print("❌ RESULT: FAIL (Performance Bottlenecks Detected)")

if __name__ == "__main__":
    asyncio.run(test_performance())
