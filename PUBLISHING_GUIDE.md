# GitHub에 배포하는 방법

## 1. 저장소 생성

GitHub에서 **New repository**를 선택하고 원하는 저장소 이름(예: `sesuni-calculator`)으로 생성합니다. **README를 자동 생성하지 않아도 됩니다**(패키지에 이미 포함되어 있습니다).

## 2. 소스 파일 업로드

제공된 `Sesuni_Calculator_v0.5.36_GitHub_Repository.zip`의 압축을 풀고 **안의 파일과 폴더 전체**를 저장소 루트에 업로드하세요. **ZIP 파일만 저장소에 올리면 README·문서 링크가 자동으로 표시되지 않습니다.**

Git 사용 예시(저장소 URL을 실제 본인의 주소로 교체):

```bash
git init
git add .
git commit -m "Release v0.5.36 source and documentation"
git branch -M main
git remote add origin https://github.com/OWNER/REPO.git
git push -u origin main
```

## 3. 릴리스 만들기

1. 저장소의 **Releases → Draft a new release**를 선택합니다.
2. 새 태그 `v0.5.36`을 만듭니다.
3. 제목은 `세순이 계산기 v0.5.36`으로 지정합니다.
4. `RELEASE_NOTES_v0.5.36.md`의 내용을 릴리스 설명에 붙여 넣습니다.
5. **소스 ZIP**인 `Sesuni_Calculator_v0.5.36_PC_build.zip` 또는 이 저장소의 소스 ZIP을 첨부합니다.
6. Windows에서 EXE를 직접 빌드·테스트했다면 그때 **검증한 EXE**를 추가로 첨부할 수 있습니다.

## 4. 릴리스 전에 확인할 것

- Windows에서 `build_windows.bat` 실행 및 EXE 생성 여부
- EXE 실행·탭 전환·보험/세금 계산·날짜계산·계산기록·복사 기능
- `%APPDATA%\DateCalculatorKR\settings.json` 생성·기록 저장·13건 제한
- 웹 바로가기 동작, 아이콘 표시(다음은 패키지 내 D 아이콘)
- 사용한 이미지/아이콘 등의 배포 권한, 저작권 및 라이선스 정책
- 실제 적용 시점의 세법·보험 요율·최저임금 기준 적합성

**라이선스 선택:** 배포자가 직접 결정하기 전까지 `LICENSE`는 추가하지 않았습니다. 제3자 리소스가 포함되어 있으므로 권리 확인이 필요합니다.
