import importlib.util
import json
from pathlib import Path

cb = json.loads(Path("work/font/final_v1/codebook.json").read_text(encoding="utf-8"))
spec = importlib.util.spec_from_file_location("enc", "work/research/encode_custom_euc28.py")
enc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(enc)

texts = [
    "완료", "초기화",
    "게임에 사용할\n컨트롤러를 설정합니다.\n컨트롤러 버튼을 누르면\n확정됩니다.",
    "컨트롤러", "진동", "자막", "커서 기억", "시점 회전", "글 속도",
    "BGM 음량", "SE 음량", "음성량", "화면 떨림", "ON", "OFF",
    "느림", "보통", "빠름", "즉시", "무음", "최대", "최소", "일반", "반전",
    "사용할 컨트롤러를 설정합니다", "컨트롤러 진동을 설정합니다",
]

for text in texts:
    try:
        payload = enc.encode_text(text, cb)
        print(len(payload), repr(text), payload.hex().upper())
    except Exception as exc:
        print("ERR", repr(text), exc)
