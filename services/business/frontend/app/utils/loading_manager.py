import streamlit as st
import time
import logging
from typing import Optional, Callable, Any
from contextlib import contextmanager

logger = logging.getLogger(__name__)

class GlobalLoadingManager:
    """전역 로딩 상태 관리 클래스 - 간소화된 버전"""
    
    def __init__(self):
        self.init_loading_state()
    
    def init_loading_state(self):
        """로딩 상태 초기화"""
        if "global_loading" not in st.session_state:
            st.session_state.global_loading = False
        if "loading_message" not in st.session_state:
            st.session_state.loading_message = "🔄 시스템 로딩 중..."
        if "loading_progress" not in st.session_state:
            st.session_state.loading_progress = 0
        if "page_ready" not in st.session_state:
            st.session_state.page_ready = True
        if "is_loading" not in st.session_state:
            st.session_state.is_loading = False
        if "loading_type" not in st.session_state:
            st.session_state.loading_type = None
    
    def show_simple_loading(self, message: str = "🔄 로딩 중...", duration: float = 1.0):
        """기본 Streamlit 스피너 사용 - 중앙 정렬"""
        st.session_state.global_loading = True
        st.session_state.is_loading = True
        st.session_state.loading_message = message
        
        # 중앙 정렬을 위한 컬럼
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col2:
            with st.spinner(message):
                time.sleep(duration)
        
        st.session_state.global_loading = False
        st.session_state.is_loading = False
        st.session_state.page_ready = True
    
    def show_progress_loading(self, steps: list, step_duration: float = 0.5):
        """진행률 표시 로딩 - 중앙 정렬 (Streamlit 네이티브 방식)"""
        st.session_state.global_loading = True
        st.session_state.is_loading = True
        total_steps = len(steps)
        
        # 중앙 정렬을 위한 컬럼 생성
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            st.markdown(
                "<div style='text-align: center; margin: 2rem 0;'>"
                "<h4 style='margin-bottom: 1rem; color: #374151;'>📊 로딩 중...</h4>"
                "</div>", 
                unsafe_allow_html=True
            )
            
            # 고정된 컨테이너들
            progress_bar = st.progress(0)
            status_text = st.empty()
            percentage_text = st.empty()
            
            for i, step in enumerate(steps):
                progress = (i + 1) / total_steps
                progress_percentage = int(progress * 100)
                
                # 프로그레스 바 업데이트
                progress_bar.progress(progress)
                
                # 상태 텍스트 업데이트
                status_text.markdown(
                    f"<div style='text-align: center; margin: 1rem 0; font-size: 1rem; color: #6b7280;'>{step}</div>", 
                    unsafe_allow_html=True
                )
                
                # 퍼센트 표시 업데이트
                percentage_text.markdown(
                    f"<div style='text-align: center; font-weight: bold; color: #3b82f6; font-size: 1.2rem;'>{progress_percentage}%</div>", 
                    unsafe_allow_html=True
                )
                
                st.session_state.loading_progress = progress_percentage
                time.sleep(step_duration)
            
            # 완료 후 정리
            time.sleep(0.5)
            progress_bar.empty()
            status_text.empty()
            percentage_text.empty()
        
        st.session_state.global_loading = False
        st.session_state.is_loading = False
        st.session_state.page_ready = True
    
    def show_loading_with_info(self, message: str = "🔄 로딩 중...", info_text: str = None, duration: float = 1.0):
        """정보 텍스트와 함께 로딩 - 중앙 정렬"""
        st.session_state.global_loading = True
        
        # 중앙 정렬을 위한 컬럼
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            # 로딩 컨테이너 생성
            loading_container = st.container()
            
            with loading_container:
                # 중앙 정렬된 로딩 박스
                info_html = f'<div style="font-size: 0.9rem; color: #6b7280;">{info_text}</div>' if info_text else ''
                st.markdown(f"""
                <div style="
                    background: white;
                    padding: 1.5rem;
                    border-radius: 10px;
                    box-shadow: 0 4px 20px rgba(0,0,0,0.1);
                    text-align: center;
                    border: 1px solid #e5e7eb;
                    margin: 2rem 0;
                ">
                    <div style="
                        font-size: 1.1rem;
                        font-weight: 600;
                        color: #374151;
                        margin-bottom: 0.5rem;
                    ">{message}</div>
                    {info_html}
                </div>
                """, unsafe_allow_html=True)
                
                # 스피너 추가
                with st.spinner(""):
                    time.sleep(duration)
            
            # 컨테이너 정리
            loading_container.empty()
        
        st.session_state.global_loading = False
        st.session_state.page_ready = True
    
    def show_custom_gauge_loading(self, steps: list, step_duration: float = 0.5):
        """커스텀 게이지바 로딩 - 단일 게이지바 업데이트 방식"""
        st.session_state.global_loading = True
        st.session_state.is_loading = True
        total_steps = len(steps)
        
        # 중앙 정렬
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            # 스타일링된 로딩 헤더
            # st.markdown("""
            # <div style="
            #     text-align: center; 
            #     margin: 2rem 0 1rem 0;
            #     padding: 1rem;
            #     background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            #     border-radius: 10px;
            #     color: white;
            # ">
            #     <h4 style="margin: 0; color: white;">🚀 진행 상황</h4>
            # </div>
            # """, unsafe_allow_html=True)
            
            # 고정된 컨테이너들 생성
            progress_container = st.empty()
            status_container = st.empty()
            percentage_container = st.empty()
            
            # CSS 스타일 한 번만 추가
            st.markdown("""
            <style>
            @keyframes shimmer {
                0% { transform: translateX(-100%); }
                100% { transform: translateX(100%); }
            }
            .progress-bar-container {
                background: #f3f4f6;
                border-radius: 25px;
                padding: 3px;
                margin: 1rem 0;
                box-shadow: inset 0 2px 4px rgba(0,0,0,0.1);
            }
            .progress-bar-fill {
                height: 20px;
                border-radius: 25px;
                transition: all 0.5s ease;
                position: relative;
                overflow: hidden;
            }
            .shimmer-effect {
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: linear-gradient(90deg, transparent 0%, rgba(255,255,255,0.3) 50%, transparent 100%);
                animation: shimmer 2s infinite;
            }
            </style>
            """, unsafe_allow_html=True)
            
            for i, step in enumerate(steps):
                progress = (i + 1) / total_steps
                progress_percentage = int(progress * 100)
                
                # 프로그레스 바 업데이트
                progress_container.markdown(f"""
                <div class="progress-bar-container">
                    <div class="progress-bar-fill" style="
                        background: linear-gradient(90deg, #4ade80 0%, #22c55e {progress_percentage}%, #f3f4f6 {progress_percentage}%);
                        width: 100%;
                    ">
                        <div class="shimmer-effect"></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # 상태 텍스트 업데이트
                status_container.markdown(f"""
                <div style="
                    text-align: center;
                    margin: 0.5rem 0;
                    color: #374151;
                    font-weight: 500;
                    font-size: 1rem;
                ">{step}</div>
                """, unsafe_allow_html=True)
                
                # 퍼센트 표시 업데이트
                percentage_container.markdown(f"""
                <div style="
                    text-align: center;
                    font-size: 1.5rem;
                    font-weight: bold;
                    color: #22c55e;
                    margin: 1rem 0;
                ">{progress_percentage}%</div>
                """, unsafe_allow_html=True)
                
                st.session_state.loading_progress = progress_percentage
                time.sleep(step_duration)
            
            # 완료 메시지
            st.markdown("""
            <div style="
                text-align: center;
                padding: 1rem;
                background: #dcfce7;
                border-radius: 10px;
                color: #166534;
                font-weight: bold;
                margin-top: 1rem;
                animation: fadeIn 0.5s ease-out;
            ">
                ✅ 완료되었습니다!
            </div>
            <style>
            @keyframes fadeIn {
                from { opacity: 0; transform: translateY(10px); }
                to { opacity: 1; transform: translateY(0); }
            }
            </style>
            """, unsafe_allow_html=True)
            
            time.sleep(0.8)  # 완료 메시지 표시 시간
        
        st.session_state.global_loading = False
        st.session_state.is_loading = False
        st.session_state.page_ready = True
    
    @contextmanager
    def loading_context(self, message: str = "🔄 처리 중..."):
        """컨텍스트 매니저로 로딩 상태 관리"""
        st.session_state.global_loading = True
        st.session_state.loading_message = message
        
        try:
            with st.spinner(message):
                yield
        finally:
            st.session_state.global_loading = False
            st.session_state.page_ready = True
    
    def is_loading(self) -> bool:
        """현재 로딩 상태 확인"""
        return st.session_state.get("global_loading", False)
    
    def is_page_ready(self) -> bool:
        """페이지 준비 상태 확인"""
        return st.session_state.get("page_ready", True)
    
    def reset_loading_state(self):
        """로딩 상태 리셋"""
        st.session_state.global_loading = False
        st.session_state.is_loading = False
        st.session_state.page_ready = True
        st.session_state.loading_progress = 0
        st.session_state.loading_type = None
    
    def show_auth_loading(self):
        """인증 전용 로딩 - 커스텀 게이지 사용"""
        steps = [
            "🔐 인증 정보 확인 중...",
            "👤 사용자 정보 로드 중...",
            "🏢 대시보드 준비 중...",
            "✅ 로딩 완료!"
        ]
        self.show_custom_gauge_loading(steps, 0.6)
    
    def show_page_transition_loading(self, from_page: str, to_page: str):
        """페이지 전환 로딩"""
        clean_to_page = to_page.replace("💼 ", "").replace("⚙️ ", "").replace(" 대시보드", "")
        message = f"📄 {clean_to_page}로 이동 중..."
        self.show_simple_loading(message, 0.6)
    
    def show_refresh_loading(self):
        """새로고침 전용 로딩 - 커스텀 게이지 사용"""
        steps = [
            "🔄 페이지 새로고침 중...",
            "📊 데이터 동기화 중...",
            "✅ 준비 완료!"
        ]
        self.show_custom_gauge_loading(steps, 0.4)
    
    def show_custom_loading(self, title: str, steps: list = None, duration: float = 1.0, use_custom_gauge: bool = False):
        """커스텀 로딩 (단계별 또는 단순)"""
        if steps:
            if use_custom_gauge:
                self.show_custom_gauge_loading(steps, duration / len(steps))
            else:
                self.show_progress_loading(steps, duration / len(steps))
        else:
            self.show_simple_loading(title, duration)


# 전역 인스턴스 생성
loading_manager = GlobalLoadingManager()

# 편의 함수들
def show_loading(message: str = "🔄 로딩 중...", duration: float = 1.0):
    """간편 로딩 표시"""
    loading_manager.show_simple_loading(message, duration)

def show_auth_loading():
    """인증 로딩 - 커스텀 게이지"""
    loading_manager.show_auth_loading()

def show_refresh_loading():
    """새로고침 로딩 - 커스텀 게이지"""
    loading_manager.show_refresh_loading()

def show_page_loading(to_page: str):
    """페이지 전환 로딩"""
    loading_manager.show_page_transition_loading("", to_page)

def show_progress_loading(steps: list, step_duration: float = 0.5):
    """진행률 로딩"""
    loading_manager.show_progress_loading(steps, step_duration)

def show_gauge_loading(steps: list, step_duration: float = 0.5):
    """커스텀 게이지 로딩"""
    loading_manager.show_custom_gauge_loading(steps, step_duration)

def loading_context(message: str = "🔄 처리 중..."):
    """로딩 컨텍스트"""
    return loading_manager.loading_context(message)

def with_loading(message: str = "🔄 처리 중..."):
    """로딩 데코레이터"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            with loading_context(message):
                return func(*args, **kwargs)
        return wrapper
    return decorator

def is_loading() -> bool:
    """로딩 상태 확인"""
    return loading_manager.is_loading()

def reset_loading():
    """로딩 상태 리셋"""
    loading_manager.reset_loading_state()

def set_loading_state(loading_type: str = None):
    """로딩 상태 설정"""
    st.session_state.is_loading = True
    st.session_state.loading_type = loading_type

def clear_loading_state():
    """로딩 상태 해제"""
    st.session_state.is_loading = False
    st.session_state.loading_type = None

def is_app_loading() -> bool:
    """앱이 로딩 중인지 확인"""
    return st.session_state.get("is_loading", False)

def get_loading_type() -> str:
    """현재 로딩 타입 반환"""
    return st.session_state.get("loading_type", None)

# 사용 예시들
def example_usage():
    """사용 예시"""
    
    # 1. 기본 로딩
    show_loading("데이터 로드 중...", 2.0)
    
    # 2. 진행률 로딩
    steps = ["1단계 처리 중...", "2단계 처리 중...", "완료!"]
    show_progress_loading(steps, 0.5)
    
    # 3. 커스텀 게이지 로딩
    show_gauge_loading(["준비 중...", "처리 중...", "완료!"], 0.6)
    
    # 4. 컨텍스트 매니저 사용
    with loading_context("파일 처리 중..."):
        # 여기서 실제 작업 수행
        time.sleep(2)
    
    # 5. 데코레이터 사용
    @with_loading("계산 중...")
    def heavy_calculation():
        time.sleep(3)
        return "결과"
    
    result = heavy_calculation()