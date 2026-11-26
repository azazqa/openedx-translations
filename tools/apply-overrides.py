#!/usr/bin/env python3
"""overrides/ 의 항목을 translations/ 위에 덮어씁니다.

- .po : overrides 가 앞에 오도록 msgcat --use-first 로 병합 (같은 msgid 는 overrides 우선)
- .json : overrides 의 키를 translations 파일에 덮어쓰기
- 병합 뒤 msgfmt --check-format 으로 형식을 검사합니다.

실행 환경에는 gettext(msgcat, msgfmt)가 필요합니다.
"""
import json
import pathlib
import shutil
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC, DST = ROOT / "overrides", ROOT / "translations"


def main() -> int:
    for cmd in ("msgcat", "msgfmt"):
        if shutil.which(cmd) is None:
            sys.exit(f"{cmd} 필요 (gettext 설치)")
    if not SRC.is_dir():
        sys.exit("overrides/ 가 없습니다")

    applied = 0
    for ov in sorted(SRC.rglob("*")):
        if not ov.is_file():
            continue
        target = DST / ov.relative_to(SRC)
        target.parent.mkdir(parents=True, exist_ok=True)
        if ov.suffix == ".po":
            if target.exists():
                tmp = target.with_name(target.name + ".tmp")
                subprocess.check_call(
                    ["msgcat", "--use-first", "--no-wrap", str(ov), str(target), "-o", str(tmp)]
                )
                tmp.replace(target)
            else:
                shutil.copy2(ov, target)
            subprocess.check_call(["msgfmt", "--check-format", "-o", "/dev/null", str(target)])
        elif ov.suffix == ".json":
            base = json.loads(target.read_text(encoding="utf-8")) if target.exists() else {}
            base.update(json.loads(ov.read_text(encoding="utf-8")))
            # 키 순서는 upstream 파일을 그대로 두고 새 키만 뒤에 붙입니다 (diff 를 줄이기 위해 정렬하지 않음).
            target.write_text(
                json.dumps(base, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
        else:
            sys.exit(f"지원하지 않는 형식: {ov}")
        applied += 1
        print(f"applied {ov.relative_to(SRC)}")
    print(f"총 {applied}개 적용")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
