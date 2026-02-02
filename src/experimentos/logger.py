"""
로깅 설정

애플리케이션 전체에서 사용할 로거를 설정하는 모듈
"""

import logging
import sys


def setup_logger(name: str = "experimentos", level: int = logging.INFO) -> logging.Logger:
    """
    로거 설정
    
    Args:
        name: 로거 이름 (기본값: "experimentos")
        level: 로깅 레벨 (기본값: logging.INFO)
    
    Returns:
        logging.Logger: 설정된 로거 객체
    """
    logger = logging.getLogger(name)
    
    # 이미 핸들러가 설정되어 있으면 중복 방지
    if logger.handlers:
        return logger
    
    logger.setLevel(level)
    
    # 콘솔 핸들러
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)
    
    # 포맷 설정
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    handler.setFormatter(formatter)
    
    logger.addHandler(handler)
    
    return logger
