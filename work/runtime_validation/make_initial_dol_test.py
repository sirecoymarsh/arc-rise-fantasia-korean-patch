import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "work/disc_extracted/DATA/sys/main.dol"
OUTPUT = ROOT / "work/final_runtime_staging/riivolution_sd/arc_rise_fantasia_ko_full/files/sys/main.dol"
CODEBOOK = ROOT / "work/font/final_v1/codebook.json"

PATCHES = [
    (0x3D10FA, "設定終了", "완료"),
    (0x3D1103, "初期設定", "초기화"),
    (0x3D110C, "ゲームで使用する\nコントローラを設定します。\nコントローラのボタンを押せば\n確定されます。", "게임에 사용할\n컨트롤러를 설정합니다.\n컨트롤러 버튼을 누르면\n확정됩니다."),
    (0x3D1164, "%sを\n操作コントローラに設定しました。", "%s를\n조작 컨트롤러로 설정했습니다."),
    (0x3D118A, "コントローラ", "컨트롤러"),
    (0x3D1197, "振動", "진동"),
    (0x3D119C, "字幕", "자막"),
    (0x3D11A1, "カーソル記憶", "커서 기억"),
    (0x3D11AE, "カメラ回転", "시점 회전"),
    (0x3D11B9, "文字速度", "글 속도"),
    (0x3D11C2, "ＢＧＭ音量", "BGM 음량"),
    (0x3D11CD, "ＳＥ音量", "SE 음량"),
    (0x3D11D6, "音声音量", "음성량"),
    (0x3D11DF, "フリッカーレベル", "화면 떨림"),
    (0x3D11F0, "ＯＮ", "ON"),
    (0x3D11F5, "ＯＦＦ", "OFF"),
    (0x3D11FC, "遅い", "느림"),
    (0x3D1201, "普通", "보통"),
    (0x3D1206, "早い", "빠름"),
    (0x3D120B, "瞬間", "즉시"),
    (0x3D1210, "無音", "무음"),
    (0x3D1215, "最大", "최대"),
    (0x3D121A, "最小", "최소"),
    (0x3D121F, "通常", "일반"),
    (0x3D1224, "反転", "반전"),
    (0x3D1229, "使用するコントローラを設定します", "사용할 컨트롤러를 설정합니다"),
    (0x3D124A, "コントローラの振動を設定します", "컨트롤러 진동을 설정합니다"),
    (0x3D1269, "デモシーンの字幕の表示／非表示を\n設定します", "데모 자막 표시를\n설정합니다"),
    (0x3D1295, "戦闘中のメニューのカーソル位置の\n保存／リセットを設定します", "전투 메뉴 커서 위치의\n저장 여부를 설정합니다"),
    (0x3D12D1, "ワールドでのカメラの回転方向を\n設定します", "월드 카메라 회전 방향을\n설정합니다"),
    (0x3D12FB, "メッセージの表示速度を設定します", "메시지 표시 속도를 설정합니다"),
    (0x3D131C, "ＢＧＭの音量調整をします", "BGM 음량을 조절합니다"),
    (0x3D1335, "ＳＥの音量調整をします", "SE 음량을 조절합니다"),
    (0x3D134C, "音声の音量調整をします", "음성량을 조절합니다"),
    (0x3D1363, "フリッカーフィルタのレベルを設定します", "화면 떨림 수준을 설정합니다"),
]


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def main() -> None:
    cb = json.loads(CODEBOOK.read_text(encoding="utf-8"))
    spec = importlib.util.spec_from_file_location("arf_encoder", ROOT / "work/research/encode_custom_euc28.py")
    enc = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(enc)
    data = bytearray(SOURCE.read_bytes())
    report = []
    for offset, source, target in PATCHES:
        raw = source.encode("euc_jp")
        actual = bytes(data[offset:offset + len(raw)])
        if actual != raw or data[offset + len(raw)] != 0:
            raise ValueError(f"source mismatch at 0x{offset:X}: {actual.hex()} != {raw.hex()}")
        payload = enc.encode_text(target, cb)
        if len(payload) > len(raw):
            raise ValueError(f"overflow at 0x{offset:X}: {len(payload)} > {len(raw)} for {target!r}")
        data[offset:offset + len(raw)] = payload + bytes(len(raw) - len(payload))
        report.append({"offset": offset, "source": source, "translation_ko": target,
                       "capacity": len(raw), "encoded_length": len(payload), "replacement_hex": payload.hex().upper()})
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_bytes(data)
    out_report = ROOT / "work/runtime_validation/initial_dol_test_report.json"
    out_report.write_text(json.dumps({"source_sha256": sha256(SOURCE.read_bytes()),
                                      "output_sha256": sha256(data), "patch_count": len(report),
                                      "patches": report}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(OUTPUT), "sha256": sha256(data), "patch_count": len(report)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
