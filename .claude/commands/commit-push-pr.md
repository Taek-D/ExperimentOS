# Commit, Push & PR

변경사항을 커밋하고 PR을 생성합니다.

## 수행 작업

1. `git status`로 변경된 파일 확인
2. `git diff`로 변경 내용 분석
3. 변경 사항에 맞는 커밋 메시지 작성 (conventional commits)
4. 관련 파일만 `git add`
5. `git commit` 실행
6. `git push` 실행
7. `gh pr create`로 PR 생성

## 커밋 메시지 규칙

- `feat:` 새 기능
- `fix:` 버그 수정
- `refactor:` 리팩토링
- `test:` 테스트 추가/수정
- `docs:` 문서 변경
- `chore:` 설정/빌드 변경

## 주의사항

- `.env`, credentials 파일은 커밋하지 않음
- 테스트 통과 여부를 먼저 확인: `python -m pytest tests/ -v`
