#!/usr/bin/env python3
import asyncio, aiohttp, json, os, time
from pathlib import Path

# 20 个提示词
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

API_BASE   = "https://open.bigmodel.cn/api/paas/v4/videos/generations"
POLL_BASE  = "https://open.bigmodel.cn/api/paas/v4/async-result/"
HEADERS = {
    "Authorization": "Bearer 293c8***********d415a",
    "Content-Type": "application/json"
}

TASK_IDS = []
VID_PATHS = []

async def submit(prompt):
    async with aiohttp.ClientSession() as sess:
        async with sess.post(API_BASE, headers=HEADERS, json={
            "model": "cogvideox-flash",
            "prompt": prompt,
            "duration": 4,
            "aspect_ratio": "16:9"
        }, timeout=30) as r:
            data = await r.json()
            tid = data.get("data", {}).get("task_id")
            if tid:
                print(f"✅ 提交成功 task_id={tid[:12]}... index={len(TASK_IDS)}")
                TASK_IDS.append(tid)
            else:
                print("❌ 提交失败", await r.text())

async def poll_one(tid):
    url = POLL_BASE + tid
    out_dir = Path(__file__).parent / "vids_raw"
    out_dir.mkdir(parents=True, exist_ok=True)

    async with aiohttp.ClientSession() as sess:
        for i in range(50):
            await asyncio.sleep(8)
            async with sess.get(url, headers=HEADERS, timeout=30) as r:
                data = await r.json()
                status = data.get("data", {}).get("status")
                if status == "SUCCESS":
                    result_url = data["data"]["result_url"]
                    dest = out_dir / f"video_{tid[:8]}.mp4"
                    async with sess.get(result_url) as vr:
                        chunk = await vr.read()
                    dest.write_bytes(chunk)
                    print(f"✅ 下载完成 -> {dest}")
                    VID_PATHS.append(str(dest.absolute()))
                    return True
                if status == "FAILED":
                    print(f"💥 {tid[:8]} 生成失败")
                    return False
        return False

async def main():
    # 先提交
    await asyncio.gather(*[submit(p) for p in prompts])
    print(f"✅ 所有任务提交完毕，共 {len(TASK_IDS)} 个")

    # 等待 16s 后开始轮询
    await asyncio.sleep(16)
    await asyncio.gather(*[poll_one(tid) for tid in TASK_IDS])

if __name__ == "__main__":
    asyncio.run(main())
    print("最终视频清单（可用于拼接）：")
    print("\n".join(VID_PATHS))
