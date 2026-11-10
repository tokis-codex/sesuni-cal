# 세순이 계산기 (Sesuni Calculator) 🐧

**Windows용 계산기 · 세율/기장의무 참고표 · 날짜 및 납부지연가산세 계산**

현재 버전: **v0.5.36** | 개발 언어: **Python** | GUI: **PySide6** | 대상 OS: **Windows**

> **배포 안내:** 이 저장소는 **소스코드와 Windows EXE 빌드 스크립트**를 제공합니다. EXE는 이 저장소에서 직접 빌드해야 합니다. 현재 패키지에는 미리 빌드된 EXE가 들어 있지 않습니다.
>
> **유의:** 세금·4대보험·가산세 계산 결과에는 추정치나 간략화한 기준이 포함됩니다. 실제 신고/납부/급여 지급에 사용하기 전에 관계 법령과 공식 기관 자료를 확인하세요.

## 화면 미리보기

아래 이미지는 **v0.5.32에서 실제 촬영한 화면**입니다. v0.5.36에서도 기본 화면 구성은 유지되지만, 일부 계산 결과·동작은 변경되었습니다.

| 세율 및 보험료 | 기장의무 | 양도·상속·증여 |
|:--:|:--:|:--:|
| ![세율 화면](docs/screenshots/01_rates.png) | ![기장의무 화면](docs/screenshots/02_bookkeeping.png) | ![양도상증 화면](docs/screenshots/03_capital_gift_inheritance.png) |

| 날짜계산 | 계산기록 |
|:--:|:--:|
| ![날짜계산 화면](docs/screenshots/04_date_penalty.png) | ![계산기록 화면](docs/screenshots/05_history.png) |

## 주요 기능

- **일반 계산기:** `+`, `−`, `×`, `÷`, `%`, 부호 변경, 지우기, `000`, 메모리 `MC`/`MR`/`M+`/`M−`.
- **소수점 표시:** 사칙연산 결과는 소수점 아래 **최대 3자리** 표시(반올림, 불필요한 0 생략). 내부 계산 정밀도는 유지.
- **계산기록:** 최근 **13건**까지 보관. 항목을 누르면 결과 숫자를 다시 사용할 수 있음.
- **세율등 → 세율:** 4대보험료 추산, 근로·사업소득세 및 차인지급액, 종합·법인세 기본 세율 계산. 표 영역을 클릭해 이미지 복사.
- **세율등 → 기장의무:** 기장의무 판단 참고표, 성실신고확인대상, 최저임금, 전자 발급 의무 참고표.
- **세율등 → 양도상증:** 양도세율, 장기보유특별공제, 증여/상속 세율 및 공제 참고표.
- **날짜계산:** 시작일·종료일 경과일수(초일 제외), 국세/지방세 신고분·고지분 납부지연가산세 추산. 계산식 클릭 시 텍스트 복사.
- **바로가기:** Gmail·다음·네이버 메일. 다음 아이콘은 내장 이미지로 표시(시작 시 다운로드하지 않음).

상세 조작법과 주의사항은 **[사용설명서](docs/USER_GUIDE.md)**를 참조하세요.

## Windows 실행파일 만들기

1. 페이지의 **Code → Download ZIP**으로 저장소를 내려받거나 Git으로 복제합니다.
2. Windows에 **Python 3.11~3.13**을 설치하고 `py` 런처를 사용할 수 있게 합니다.
3. 압축을 풀거나 복제한 폴더에서 **`build_windows.bat`**을 실행합니다. 최초 빌드 시 패키지 설치를 위한 인터넷 연결이 필요합니다.
4. 빌드가 성공하면 **`dist\Sesuni_Calculator.exe`**가 생성됩니다.

`build_windows.bat`은 **PySide6와 PyInstaller를 설치/갱신**한 다음, PyInstaller의 **`--onefile --windowed`** 모드로 단일 EXE를 만듭니다. *배포받는 사용자는 빌드된 EXE를 실행할 때 Python을 별도로 설치할 필요가 없습니다.*

> **검증 상태:** Python 소스 구문 검사와 배포 ZIP 구조·무결성은 점검했습니다. Windows에서의 실제 EXE 빌드, 실행 속도, GUI 화면 동작은 이 환경에서 검증하지 못했습니다.

## 소스에서 직접 실행 (개발용)

Windows 터미널에서 다음을 실행합니다.

```powershell
py -3 -m pip install PySide6
py -3 date_calculator.py
```

## 프로젝트 구성

```text
.
├── date_calculator.py         # 메인 프로그램
├── build_windows.bat          # Windows 단일 EXE 빌드
├── date_calculator.ico        # 프로그램 아이콘
├── *_fallback.png             # Gmail/다음/네이버 아이콘 리소스
├── calendar_tab.png           # 날짜계산 탭 아이콘
├── history_tab.png            # 계산기록 탭 아이콘
├── README.md                  # 이 문서
├── CHANGELOG.md               # 변경 이력
├── RELEASE_NOTES_v0.5.36.md   # GitHub Releases 설명문
├── PUBLISHING_GUIDE.md        # GitHub 배포 절차
└── docs/
    ├── USER_GUIDE.md          # 사용자 설명서
    └── screenshots/           # 실제 v0.5.32 화면 캡처
```

## 설정 및 저장 데이터

설정과 계산기록은 일반적으로 다음 위치에 저장됩니다.

```text
%APPDATA%\DateCalculatorKR\settings.json
```

계산기록은 최근 13건만 보관하며, 날짜계산 시작일의 초기값은 **실행한 연도의 1월 1일**입니다.

## 변경 이력 · 배포

- [변경 이력](CHANGELOG.md)
- [v0.5.36 릴리스 설명문](RELEASE_NOTES_v0.5.36.md)
- [GitHub 업로드 및 릴리스 등록 방법](PUBLISHING_GUIDE.md)

## 라이선스 · 저작권

**현재 별도의 LICENSE 파일은 포함하지 않았습니다.** 공개 저장소에 올렸다는 사실만으로 제3자에게 수정·재배포를 허용하는 것은 아닙니다. 오픈소스로 공개하려면 권리자가 적절한 라이선스를 별도로 결정해 추가하세요. 아이콘·폰트 등 제3자 리소스의 권리 관계도 배포 전 확인해 주세요.
