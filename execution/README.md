# Execution (실행 스크립트)

이 디렉토리에는 **Layer 3: Execution** 파일들이 포함됩니다.

## 목적

Execution 레이어는 결정론적(deterministic) Python 스크립트로 구성됩니다. 이 스크립트들은 다음을 처리합니다:

- API 호출
- 데이터 처리
- 파일 작업
- 데이터베이스 상호작용

## 스크립트 작성 원칙

1. **결정론적**: 같은 입력에 대해 항상 같은 출력을 생성
2. **테스트 가능**: 단위 테스트 작성 권장
3. **빠른 실행**: 효율적인 구현
4. **명확한 주석**: 잘 문서화된 코드

## 환경 변수

모든 API 키와 토큰은 루트 디렉토리의 `.env` 파일에 저장됩니다.

```python
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv('API_KEY_NAME')
```

## 스크립트 예시 구조

```python
"""
스크립트 제목

설명: 이 스크립트의 목적과 기능
입력: 필요한 인자들
출력: 생성되는 결과물
"""

import os
from dotenv import load_dotenv

def main():
    """메인 실행 함수"""
    # 환경 변수 로드
    load_dotenv()
    
    # 로직 구현
    pass

if __name__ == "__main__":
    main()
```

## 에러 처리

모든 스크립트는 적절한 에러 처리를 포함해야 합니다:

```python
try:
    # 위험한 작업
    result = api_call()
except APIError as e:
    print(f"API 에러 발생: {e}")
    # 에러 로깅 및 복구 로직
```

## 의존성 관리

필요한 Python 패키지는 `requirements.txt`에 명시하세요.
