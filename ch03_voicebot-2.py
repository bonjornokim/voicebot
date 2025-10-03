##### 기본 정보 입력 #####
import os
import streamlit as st
# audiorecorder 패키지 추가
from audiorecorder import audiorecorder
# OpenAI 패키지 추가 (최신 SDK)
import openai 
# 파일 삭제를 위한 패키지 추가
import os
# 시간 정보를 위한 패키지 추가
from datetime import datetime
# TTS 패키지 추가
from gtts import gTTS
# 음원 파일 재생을 위한 패키지 추가
import base64

# --- API 클라이언트 전역 변수 (함수 내에서 초기화할 것임) ---
# client는 main 함수 내에서 API 키 입력 후 초기화됩니다.

##### 기능 구현 함수 #####
def STT(client: openai.OpenAI, audio):
    """Whisper API를 사용하여 음성을 텍스트로 변환합니다."""
    # 파일 저장
    filename='input.mp3'
    # audio.export()는 IO 객체를 반환하므로, audio.export().read() 대신
    # 파일로 저장 후 API에 전달하는 방식을 사용합니다.
    audio.export(filename, format="mp3")
    
    try:
        # 음원 파일 열기 (with 문 사용으로 자동 닫기 보장)
        with open(filename, "rb") as audio_file:
            # 최신 SDK 문법: client.audio.transcriptions.create 사용
            transcript_response = client.audio.transcriptions.create(
                model="whisper-1", 
                file=audio_file
            )
        
        # 파일 삭제
        os.remove(filename)
        return transcript_response.text

    except Exception as e:
        st.error(f"STT 처리 중 오류 발생: {e}")
        if os.path.exists(filename):
            os.remove(filename)
        return "STT 오류 발생"


def ask_gpt(client: openai.OpenAI, prompt, model):
    """GPT 모델에 질문을 전달하고 답변을 받습니다."""
    try:
        # 최신 SDK 문법: client.chat.completions.create 사용
        response = client.chat.completions.create(model=model, messages=prompt)
        # 응답 구조가 변경되었으므로 .content로 접근
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"GPT API 호출 중 오류 발생: {e}")
        return "죄송합니다. GPT 응답을 받는 중에 오류가 발생했습니다."


def TTS(response):
    """gTTS를 사용하여 텍스트를 음성으로 변환하고 Streamlit에 재생합니다."""
    # gTTS 를 활용하여 음성 파일 생성
    filename = "output.mp3"
    try:
        tts = gTTS(text=response, lang="ko")
        tts.save(filename)

        # 음원 파일 자동 재생
        with open(filename, "rb") as f:
            data = f.read()
            b64 = base64.b64encode(data).decode()
            md = f"""
            <audio autoplay="true">
            <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
            </audio>
            """
            st.markdown(md, unsafe_allow_html=True)
            
        # 파일 삭제
        os.remove(filename)

    except Exception as e:
        st.error(f"TTS 처리 중 오류 발생: {e}")
        if os.path.exists(filename):
            os.remove(filename)


##### 메인 함수 #####
def main():
    # 기본 설정
    st.set_page_config(
        page_title="음성 비서 프로그램",
        layout="wide")

    # session state 초기화
    if "chat" not in st.session_state:
        st.session_state["chat"] = []

    if "messages" not in st.session_state:
        st.session_state["messages"] = [{"role": "system", "content": "You are a thoughtful assistant. Respond to all input in 250 words and answer in korea. "}]

    if "check_reset" not in st.session_state:
        st.session_state["check_reset"] = False

    # 제목 
    st.header("🔊 음성 비서 프로그램") # 아이콘 추가
    # 구분선
    st.markdown("---")
    
    # OpenAI API 클라이언트 초기화
    client = None

    # 사이드바 생성
    with st.sidebar:

        # API 키를 환경 변수에서 가져오기 (사용자 요청 사항 반영)
        '''API_KEY = os.environ.get("OPENAI_API_KEY")'''
        API_KEY = "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"

        if API_KEY:
            try:
                # API 키가 있으면 클라이언트 초기화
                client = openai.OpenAI(api_key=API_KEY)
                st.success("✅ OpenAI API 키가 환경 변수에서 로드되었습니다.")
            except Exception as e:
                st.error(f"OpenAI 클라이언트 초기화 오류: {e}")
                client = None
        else:
            st.warning("⚠️ 환경 변수 'OPENAI_API_KEY'를 설정해 주세요.")
            client = None
        
        st.markdown("---")

        # GPT 모델을 선택하기 위한 라디오 버튼 생성
        model = st.radio(label="GPT 모델", options=["gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"])
        
        st.markdown("---")

        # 리셋 버튼 생성
        if st.button(label="초기화"):
            # 리셋 코드 
            st.session_state["chat"] = []
            st.session_state["messages"] = [{"role": "system", "content": "You are a thoughtful assistant. Respond to all input in 25 words and answer in korea"}]
            st.session_state["check_reset"] = True
            
    # 기본 설명
    with st.expander("음성비서 프로그램에 관하여", expanded=True):
        st.write(
        """ 	
        - 음성비서 프로그램의 UI는 스트림릿을 활용했습니다.
        - STT(Speech-To-Text)는 OpenAI의 **Whisper AI**를 활용했습니다. 
        - 답변은 OpenAI의 **GPT** 모델을 활용했습니다. 
        - TTS(Text-To-Speech)는 구글의 **Google Translate TTS**를 활용했습니다.
        - **FFmpeg 설치 및 PATH 설정이 필요합니다.** (Streamlit 실행 전에 필수)
        """
        )

        st.markdown("")
        
    # 클라이언트가 초기화되지 않았으면 메인 로직 실행 중단
    if not client:
        st.info("💡 사용을 시작하려면 환경 변수 **OPENAI_API_KEY**를 설정해 주세요.")
        return

    # 기능 구현 공간
    col1, col2 = st.columns(2)
    with col1:
        # 왼쪽 영역 작성
        st.subheader("🎤 질문하기")
        # 음성 녹음 아이콘 추가
        # audio.duration_seconds > 0 조건은 audiorecorder가 녹음을 성공적으로 마쳤을 때만 작동합니다.
        audio = audiorecorder("클릭하여 녹음하기", "녹음중...")
        
        # 리셋 후에는 재실행을 위해 check_reset 상태를 바로 해제
        if st.session_state["check_reset"]:
            st.session_state["check_reset"] = False
            st.rerun() # 초기화 후 다시 로드

        if audio.duration_seconds > 0:
            # 음성 재생 
            st.audio(audio.export().read())
            
            # 음원 파일에서 텍스트 추출
            with st.spinner('🗣️ 음성을 텍스트로 변환 중...'):
                question = STT(client, audio)

            # 채팅을 시각화하기 위해 질문 내용 저장
            now = datetime.now().strftime("%H:%M")
            st.session_state["chat"].append(("user", now, question))
            # GPT 모델에 넣을 프롬프트를 위해 질문 내용 저장
            st.session_state["messages"].append({"role": "user", "content": question})

    with col2:
        # 오른쪽 영역 작성
        st.subheader("💬 질문/답변")
        
        # 조건: 녹음이 완료되었고 리셋 상태가 아닐 때만 답변 프로세스 실행
        if audio.duration_seconds > 0 and "user" in [c[0] for c in st.session_state["chat"]]:

            # 마지막 메시지가 사용자 질문인지 확인하여 중복 호출 방지
            if st.session_state["messages"][-1]["role"] == "user":
                with st.spinner('🤖 GPT가 답변을 생성 중...'):
                    # ChatGPT에게 답변 얻기
                    response = ask_gpt(client, st.session_state["messages"], model)

                    # GPT 모델에 넣을 프롬프트를 위해 답변 내용 저장
                    st.session_state["messages"].append({"role": "assistant", "content": response})

                    # 채팅 시각화를 위한 답변 내용 저장
                    now = datetime.now().strftime("%H:%M")
                    st.session_state["chat"].append(("bot", now, response))

                    # gTTS 를 활용하여 음성 파일 생성 및 재생
                    with st.spinner('🔊 답변을 음성으로 변환 중...'):
                        TTS(response)

        # 채팅 형식으로 시각화 하기 (항상 표시)
        for sender, time, message in st.session_state["chat"]:
            if sender == "user":
                st.write(f'<div style="display:flex;align-items:center;"><div style="background-color:#007AFF;color:white;border-radius:12px;padding:8px 12px;margin-right:8px;max-width:80%;word-wrap:break-word;">{message}</div><div style="font-size:0.8rem;color:gray;">{time}</div></div>', unsafe_allow_html=True)
                st.write("")
            else:
                # 봇 메시지: 배경색 #EFEFEF, 글자색 black 으로 명시적 지정
                st.write(f'<div style="display:flex;align-items:center;justify-content:flex-end;"><div style="background-color:#EFEFEF;color:black;border-radius:12px;padding:8px 12px;margin-left:8px;max-width:80%;word-wrap:break-word;">{message}</div><div style="font-size:0.8rem;color:gray;">{time}</div></div>', unsafe_allow_html=True)
                st.write("")

if __name__=="__main__":
    main()

