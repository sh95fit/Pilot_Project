import streamlit as st
import time
import logging
from typing import Optional, Callable, Any

logger = logging.getLogger(__name__)

class GlobalLoadingManager:
    """전역 로딩 상태 관리 클래스"""
    
    def __init__(self):
        self.init_loading_state()
    
    def init_loading_state(self):
        """로딩 상태 초기화"""
        if "global_loading" not in st.session_state:
            st.session_state.global_loading = True
        if "loading_message" not in st.session_state:
            st.session_state.loading_message = "🔄 시스템 로딩 중..."
        if "loading_progress" not in st.session_state:
            st.session_state.loading_progress = 0
        if "page_ready" not in st.session_state:
            st.session_state.page_ready = False
    
    def show_global_loading(self, message: str = "🔄 로딩 중...", duration: float = 1.0):
        """전역 로딩 화면 표시"""
        st.session_state.global_loading = True
        st.session_state.loading_message = message
        
        # 로딩 오버레이 HTML
        loading_html = f"""
        <div id="global-loading-overlay" style="
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(3px);
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            z-index: 10000;
            animation: fadeIn 0.3s ease-out;
        ">
            <div style="
                display: flex;
                flex-direction: column;
                align-items: center;
                gap: 1rem;
                padding: 2rem;
                background: white;
                border-radius: 15px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.1);
                border: 1px solid #e5e7eb;
            ">
                <div class="loading-spinner" style="
                    width: 50px;
                    height: 50px;
                    border: 4px solid #f3f4f6;
                    border-top: 4px solid #3b82f6;
                    border-radius: 50%;
                    animation: spin 1s linear infinite;
                "></div>
                <div style="
                    font-size: 1.1rem;
                    font-weight: 600;
                    color: #374151;
                    text-align: center;
                ">{message}</div>
                <div style="
                    font-size: 0.9rem;
                    color: #6b7280;
                    text-align: center;
                ">잠시만 기다려주세요...</div>
            </div>
        </div>
        
        <style>
        @keyframes spin {
            0% {{ transform: rotate(0deg); }}
            100% {{ transform: rotate(360deg); }}
        }
        
        @keyframes fadeIn {
            from {{ opacity: 0; }}
            to {{ opacity: 1; }}
        }
        
        @keyframes fadeOut {
            from {{ opacity: 1; }}
            to {{ opacity: 0; }}
        }
        
        .fade-out {
            animation: fadeOut 0.3s ease-out forwards;
        }
        </style>
        
        <script>
        // 로딩 완료 후 자동 제거 (JavaScript)
        setTimeout(function() {
            const overlay = document.getElementById('global-loading-overlay');
            if (overlay) {
                overlay.classList.add('fade-out');
                setTimeout(function() {
                    overlay.remove();
                }, 300);
            }
        }, {duration * 1000});
        </script>
        """
        
        # HTML 렌더링
        st.markdown(loading_html, unsafe_allow_html=True)
        
        # 로딩 시간 대기
        time.sleep(duration)
        
        # 로딩 완료
        st.session_state.global_loading = False
        st.session_state.page_ready = True
    
    def show_progressive_loading(self, steps: list, step_duration: float = 0.3):
        """진행률 표시가 있는 로딩"""
        total_steps = len(steps)
        
        for i, step in enumerate(steps):
            progress = int((i + 1) / total_steps * 100)
            st.session_state.loading_progress = progress
            
            loading_html = f"""
            <div id="progressive-loading-{i}" style="
                position: fixed;
                top: 0;
                left: 0;
                width: 100vw;
                height: 100vh;
                background: rgba(255, 255, 255, 0.95);
                backdrop-filter: blur(3px);
                display: flex;
                flex-direction: column;
                justify-content: center;
                align-items: center;
                z-index: 10000;
            ">
                <div style="
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    gap: 1.5rem;
                    padding: 2rem;
                    background: white;
                    border-radius: 15px;
                    box-shadow: 0 10px 30px rgba(0,0,0,0.1);
                    min-width: 300px;
                ">
                    <div class="loading-spinner" style="
                        width: 40px;
                        height: 40px;
                        border: 3px solid #f3f4f6;
                        border-top: 3px solid #3b82f6;
                        border-radius: 50%;
                        animation: spin 1s linear infinite;
                    "></div>
                    
                    <div style="
                        font-size: 1rem;
                        font-weight: 600;
                        color: #374151;
                        text-align: center;
                    ">{step}</div>
                    
                    <div style="width: 100%; background: #e5e7eb; border-radius: 10px; height: 6px; overflow: hidden;">
                        <div style="
                            width: {progress}%;
                            height: 100%;
                            background: linear-gradient(90deg, #3b82f6, #1d4ed8);
                            border-radius: 10px;
                            transition: width 0.3s ease;
                        "></div>
                    </div>
                    
                    <div style="
                        font-size: 0.9rem;
                        color: #6b7280;
                    ">{progress}% 완료</div>
                </div>
            </div>
            """
            
            st.markdown(loading_html, unsafe_allow_html=True)
            time.sleep(step_duration)
        
        st.session_state.global_loading = False
        st.session_state.page_ready = True
    
    def is_loading(self) -> bool:
        """현재 로딩 상태 확인"""
        return st.session_state.get("global_loading", False)
    
    def is_page_ready(self) -> bool:
        """페이지 준비 상태 확인"""
        return st.session_state.get("page_ready", False)
    
    def reset_loading_state(self):
        """로딩 상태 리셋"""
        st.session_state.global_loading = False
        st.session_state.page_ready = False
        st.session_state.loading_progress = 0
    
    def with_loading(self, func: Callable, message: str = "🔄 처리 중...", duration: float = 0.8):
        """데코레이터 방식으로 함수 실행 시 로딩 표시"""
        def wrapper(*args, **kwargs):
            try:
                # 로딩 시작
                self.show_global_loading(message, duration)
                
                # 함수 실행
                result = func(*args, **kwargs)
                
                # 로딩 완료
                return result
                
            except Exception as e:
                logger.error(f"Error in loading wrapper: {e}")
                st.session_state.global_loading = False
                raise
        
        return wrapper
    
    def show_auth_loading(self):
        """인증 전용 로딩"""
        steps = [
            "🔐 인증 정보 확인 중...",
            "👤 사용자 정보 로드 중...",
            "🏢 대시보드 준비 중...",
            "✅ 로딩 완료"
        ]
        self.show_progressive_loading(steps, 0.4)
    
    def show_page_transition_loading(self, from_page: str, to_page: str):
        """페이지 전환 로딩"""
        message = f"📄 {to_page}로 이동 중..."
        self.show_global_loading(message, 0.6)
    
    def show_refresh_loading(self):
        """새로고침 전용 로딩"""
        steps = [
            "🔄 페이지 새로고침 중...",
            "📊 데이터 동기화 중...",
            "✅ 준비 완료"
        ]
        self.show_progressive_loading(steps, 0.5)

# 전역 인스턴스 생성
loading_manager = GlobalLoadingManager()

# 편의 함수들
def show_loading(message: str = "🔄 로딩 중...", duration: float = 1.0):
    """간편 로딩 표시 함수"""
    loading_manager.show_global_loading(message, duration)

def show_auth_loading():
    """인증 로딩 표시"""
    loading_manager.show_auth_loading()

def show_refresh_loading():
    """새로고침 로딩 표시"""
    loading_manager.show_refresh_loading()

def with_loading(message: str = "🔄 처리 중...", duration: float = 0.8):
    """로딩 데코레이터"""
    def decorator(func):
        return loading_manager.with_loading(func, message, duration)
    return decorator

def is_loading() -> bool:
    """현재 로딩 중인지 확인"""
    return loading_manager.is_loading()

def reset_loading():
    """로딩 상태 리셋"""
    loading_manager.reset_loading_state()