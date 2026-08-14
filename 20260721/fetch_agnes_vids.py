#!/usr/bin/env python3
import asyncio, aiohttp, json
from pathlib import Path

prompts = [
    "蓝天白云下的雪山巅峰，8K 飞行视角环绕",
    "金色阳光洒向辽阔山谷，松林层叠起伏",
    "海拔 6000 米云海之上，积雪覆盖的山脊线",
    "高原湖泊倒映蓝天白云，明镜般的水面",
    "峡谷深处云雾缭绕，瀑布奔涌而下",
    "初升朝阳给雪峰镀金，晨雾缓缓退去",
    "秋日红叶与针叶林交错，错落有致",
    "巨大冰川断层面在夕照下闪烁寒光",
    "极目远眺云海苍茫，天地无垠",
    "长空万里，白云如絮，壮阔天幕",
    "高山草甸绿毯，缀满五彩野花",
    "悬崖边回望远山，云雾萦绕山腰",
    "夕阳余晖染红雪顶，晚霞与云层交织",
    "高原风起云涌，云海波涛壮阔",
    "积雪覆盖原始森林，树冠覆盖皑皑白雪",
    "两座雪峰之间，阳光洒入山坳",
    "蓝调冷光与暖金光交错的湖面倒影",
    "晨雾消散，重峦叠嶂渐渐显露真容",
    "风吹过雪线，尘土般的松针飞扬",
    "云海中突兀矗立的孤峰，主光位来自右侧"
]

API   = "https://apihub.agnes-ai.com/v1/video/generations"
POLL  = "https://apihub.agnes-ai.com/v1/video/generations/{}"
HEADERS = {
    "Authorization": "Bearer 2c59888356f34fd388069747b042a48f.FDYxawfGYd1o7sCZ",
    "Content-Type": "application/json"
}

out_dir = Path(__file__).parent / "vids_from_agnes"
out_dir.mkdir(parents=True, exist_ok=True)

TIDS = []
VIDS = []

async def submit(prompt: str, idx: int):
    async with aiohttp.ClientSession() as s:
        async with s.post(
            API,
            headers=HEADERS,
            json={"prompt": prompt, "model": "agnes-video-v2.0", "width": 1280, "height": 704},
            timeout=45
        ) as r:
            data = await r.json()
            tid = data.get("task_id")
            if tid:
                print(f"[{idx}] Agnes OK -> {tid[:12]}...")
                TIDS.append(tid)
            else:
                print(f"[{idx}] Agnes submit err: {await r.text()}")

async def poll(tid: str):
    url = POLL.format(tid)
    async with aiohttp.ClientSession() as s:
        for _ in range(60):
            await asyncio.sleep(12)
            async with s.get(url, headers=HEADERS, timeout=50) as r:
                j = await r.json()
                status = j.get("data", {}).get("status")
                if status == "SUCCESS":
                    result_url = j["data"]["result_url"]
                    dest = out_dir / f"agnes_{tid[:8]}.mp4"
                    async with s.get(result_url) as vr:
                        chunk = await vr.read()
                    dest.write_bytes(chunk)
                    print(f"✅ [{tid[:8]}] Agnes 生成+下载完成 -> {dest}")
                    return str(dest.absolute())
                if status == "FAILED":
                    print(f"💥 [{tid[:8]}] Agnes 生成失败")
                    return None
        return None

async def main():
    await asyncio.gather(*[submit(p, i) for i,p in enumerate(prompts)])
    print(f"✅ 已提交 Agnes {len(TIDS)}/20 个")
    await asyncio.sleep(25)
    for tid in TIDS:
        f = await poll(tid)
        if f: VIDS.append(f)
    print("清单:")
    print("\n".join(VIDS))

if __name__ == "__main__":
    asyncio.run(main())

