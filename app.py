from streamlit_folium import st_folium
from dotenv import load_dotenv
from fetch_parking import ParkingDataFetcher
from db_parking import ParkingDatabase
from fav_db import (
    create_user_fav_table,
    add_user,
    check_login,
    add_to_favorite,
    get_favorite_list,
    clear_favorites
)

import streamlit as st
import folium
from folium.plugins import BeautifyIcon
import os
import pandas as pd

# ---------- initialise favourites tables (once) ----------
create_user_fav_table()
add_user("demo", "1234")  # demo account


class ParkingApp:
    def __init__(self):
        load_dotenv()
        api_key = os.getenv("KAKAO_API_KEY")
        if not api_key:
            st.error("KAKAO_API_KEY env var is missing.")
            return
        self.fetcher = ParkingDataFetcher(api_key)
        self.db = ParkingDatabase()
        
        # Initialize session state variables if not exists
        if "is_logged_in" not in st.session_state:
            st.session_state["is_logged_in"] = False
            
        if "page" not in st.session_state:
            st.session_state["page"] = "login"

    # ------------------------------------------------------ helpers
    def _perform_search(self, address, radius):
        try:
            # Clear previous search data
            self.db.clear_parking_data()
            
            x, y = self.fetcher.geocode(address)
            data = self.fetcher.fetch_parking(x, y, radius)
            self.db.save_to_db(data)
            st.session_state.update(
                center=[x, y],
                show_results=True,
                radius=radius,
                chosen_idx=None,
                fee_info=None,
                current_address=address,  # Store current address for display
            )
            st.success(f"Loaded parking lots near \"{address}\".")
        except Exception as e:
            st.error(str(e))
    
    def _get_favorite_ids(self):
        """Get the IDs of favorite parking lots for the current user"""
        if "user_id" not in st.session_state:
            return set()
        
        favs = get_favorite_list(st.session_state["user_id"])
        return {fav["id"] for fav in favs} if favs else set()
        
    # ------------------------------------------------------ Login page
    def _show_login_page(self):
        st.markdown(
            "<h1 style='text-align:center;font-size:3rem;font-weight:800;"
            "margin-top:2rem;'>주차장 찾아조 🔎</h1>",
            unsafe_allow_html=True,
        )
        
        st.markdown(
            "<h3 style='text-align:center;margin-bottom:2rem;'>로그인하여 서비스를 이용하세요</h3>",
            unsafe_allow_html=True,
        )
        
        # Center the login form
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            with st.form("login_form"):
                st.subheader("🔑 로그인")
                user_in = st.text_input("아이디", placeholder="아이디를 입력하세요")
                pw_in = st.text_input("비밀번호", type="password", placeholder="비밀번호를 입력하세요")
                
                col_login, col_signup = st.columns(2)
                
                submitted = col_login.form_submit_button("로그인", use_container_width=True)
                signup_btn = col_signup.form_submit_button("회원가입", use_container_width=True)
                
                if submitted:
                    if check_login(user_in, pw_in):
                        st.session_state["user_id"] = user_in
                        st.session_state["is_logged_in"] = True
                        st.session_state["page"] = "main"
                        st.success("로그인 성공!")
                        st.rerun()
                    else:
                        st.error("로그인 실패: 아이디 또는 비밀번호가 잘못되었습니다.")
                        
                if signup_btn:
                    st.session_state["page"] = "signup"
                    st.rerun()
            
            # Demo account info
            st.info("데모 계정: 아이디 = demo / 비밀번호 = 1234")
            
    # ------------------------------------------------------ Signup page
    def _show_signup_page(self):
        st.markdown(
            "<h1 style='text-align:center;font-size:3rem;font-weight:800;"
            "margin-top:2rem;'>회원가입</h1>",
            unsafe_allow_html=True,
        )
        
        # Center the signup form
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            with st.form("signup_form"):
                st.subheader("새 계정 만들기")
                new_user = st.text_input("아이디", placeholder="새 아이디를 입력하세요")
                new_pw = st.text_input("비밀번호", type="password", placeholder="새 비밀번호를 입력하세요")
                confirm_pw = st.text_input("비밀번호 확인", type="password", placeholder="비밀번호를 다시 입력하세요")
                
                col_submit, col_back = st.columns(2)
                
                submit_btn = col_submit.form_submit_button("계정 만들기", use_container_width=True)
                back_btn = col_back.form_submit_button("뒤로 가기", use_container_width=True)
                
                if submit_btn:
                    if not new_user or not new_pw:
                        st.error("아이디와 비밀번호를 모두 입력해주세요.")
                    elif new_pw != confirm_pw:
                        st.error("비밀번호가 일치하지 않습니다.")
                    else:
                        add_user(new_user, new_pw)
                        st.success("회원가입 성공! 이제 로그인할 수 있습니다.")
                        st.session_state["page"] = "login"
                        st.rerun()
                        
                if back_btn:
                    st.session_state["page"] = "login"
                    st.rerun()

    # ------------------------------------------------------ Main parking app UI
    def _show_main_app(self):
        # Header with user info and logout button
        col_title, col_user = st.columns([4, 1])
        
        with col_title:
            st.markdown(
                "<h1 style='font-size:2.5rem;font-weight:800;"
                "margin-top:1rem;'>어디 근처에 주차하시나요?</h1>",
                unsafe_allow_html=True,
            )
        
        with col_user:
            st.markdown(f"**{st.session_state['user_id']}**님 환영합니다!")
            if st.button("로그아웃"):
                # Clear session state and return to login
                for key in list(st.session_state.keys()):
                    if key not in ["page", "is_logged_in"]:
                        del st.session_state[key]
                st.session_state["is_logged_in"] = False
                st.session_state["page"] = "login"
                st.rerun()

        # ---------- address + search ----------
        radius_default = 700
        radius = st.session_state.get("radius", radius_default)

        with st.form("search_form"):
            address = st.text_input(
                "", placeholder="목적지 주소를 입력하세요",
                label_visibility="collapsed"
            )
            submitted = st.form_submit_button("📡 주차장 검색")

        if submitted and address:
            self._perform_search(address, radius)
        elif submitted:
            st.warning("Please enter an address first.")

        # ---------- results ----------
        if st.session_state.get("show_results"):
            # Display current location
            current_address = st.session_state.get("current_address", "Unknown location")
            st.markdown(f"### 현재 검색 위치: **{current_address}**")
            
            radius = st.slider(
                "📏 검색 반경 (m)", 500, 1000, st.session_state["radius"], 100
            )
            if radius != st.session_state["radius"] and "current_address" in st.session_state:
                # Re-search with new radius but same address
                self._perform_search(st.session_state["current_address"], radius)

            df = self.db.get_parking_data()
            if df.empty:
                st.info("No results.")
                return

            cx, cy = st.session_state["center"]

            # Get favorite parking lot IDs for the current user (if logged in)
            favorite_ids = self._get_favorite_ids()

            # folium map
            m = folium.Map(location=[cy, cx], zoom_start=15)
            
            # Add current location as a red marker
            folium.Marker(
                [cy, cx], 
                popup=folium.Popup("현재 위치"), 
                icon=folium.Icon(color="red", icon="home")
            ).add_to(m)
            
            # Add markers for parking lots
            for _, r in df.iterrows():
                lot_id = int(r["id"])
                is_favorite = lot_id in favorite_ids
                
                if is_favorite:
                    # Star icon for favorites
                    icon = BeautifyIcon(
                        icon_shape="marker",
                        icon="star",
                        border_color="gold",
                        background_color="lightblue",
                        text_color="darkblue",
                        inner_icon_style="font-size:12px;padding-top:2px;"
                    )
                else:
                    # Regular blue icon for non-favorites
                    icon = folium.Icon(color="blue", icon="info-sign")
                
                # Add marker with appropriate icon
                popup_content = f"""
                <b>{r["name"]}</b><br>
                거리: {r["distance"]}m<br>
                {'⭐ 즐겨찾기' if is_favorite else ''}
                """
                
                folium.Marker(
                    [float(r["y"]), float(r["x"])],
                    popup=folium.Popup(popup_content),
                    icon=icon,
                ).add_to(m)

            col_list, col_map, col_info = st.columns([3, 6, 3], gap="large")

            # ---------- list column ----------
            with col_list:
                lot_count = len(df)
                st.subheader(f"🔍 주차장 선택 ({lot_count}개)")
                
                # Add instruction text
                st.info("목록에서 주차장을 클릭하세요")
                
                # Get data for display in buttons
                display_df = (
                    df[["id", "name", "distance"]]
                    .rename(columns={"name": "주차장명", "distance": "거리(m)"})
                    .reset_index(drop=True)
                )
                
                # Create a container with scrollable region for selection buttons
                with st.container(height=500, border=False):
                    for idx, row in display_df.iterrows():
                        # Create a unique button for each row
                        lot_name = row["주차장명"]
                        lot_dist = row["거리(m)"]
                        lot_id = int(row["id"])
                        
                        # Check if this lot is a favorite
                        is_favorite = lot_id in favorite_ids
                        
                        # Use a key with region info to avoid conflicts
                        button_key = f"lot_{idx}_{current_address}"
                        
                        # Highlight the selected button
                        is_selected = st.session_state.get("chosen_idx") == idx
                        button_style = "primary" if is_selected else "secondary"
                        
                        # Add star emoji to favorites in the list
                        button_text = f"{idx+1}. {'⭐ ' if is_favorite else ''}{lot_name} ({lot_dist}m)"
                        
                        if st.button(
                            button_text, 
                            key=button_key, 
                            use_container_width=True,
                            type=button_style
                        ):
                            st.session_state["chosen_idx"] = idx
                            st.session_state["fee_info"] = None  # reset old scrape
                            st.rerun()

            # ---------- map column ----------
            with col_map:
                st.subheader("🗺️ 지도에서 보기")
                st_folium(m, height=600, use_container_width=True)
                
                # Add a small legend for the icons
                with st.expander("지도 아이콘 설명", expanded=False):
                    st.markdown("""
                    - 🔴 빨간색 아이콘: 현재 위치
                    - 🔵 파란색 아이콘: 일반 주차장
                    - ⭐ 별 아이콘: 즐겨찾기 주차장
                    """)

            # ---------- info column ----------
            with col_info:
                st.subheader("ℹ️ 선택한 주차장")

                idx = st.session_state.get("chosen_idx")  # row position (0-based)
                if idx is None:
                    st.info("좌측 목록에서 주차장을 선택하세요.")
                else:
                    row = df.iloc[idx]  # ← always correct row
                    lot_id = int(row["id"])
                    is_favorite = lot_id in favorite_ids

                    st.markdown(f"**주차장명**: {row['name']} {' ⭐' if is_favorite else ''}")
                    st.markdown(f"**주소**: {row.get('address', '-')}")
                    st.markdown(f"**거리**: {row['distance']} m")
                    url = row.get("url")
                    st.markdown(
                        "**상세 링크**: " + (f"[바로가기]({url})" if url else "-"),
                        unsafe_allow_html=True,
                    )

                    # ⭐ favourite button
                    if is_favorite:
                        st.success("⭐ 즐겨찾기에 추가된 주차장입니다")
                    else:
                        if st.button("⭐ 즐겨찾기 추가"):
                            ok = add_to_favorite(
                                st.session_state["user_id"], lot_id
                            )
                            if ok:
                                st.success("즐겨찾기에 추가되었습니다!")
                                st.rerun()  # Update the UI to show the star icon
                            else:
                                st.error("추가 실패")

                    # 📡 fee scrape button (unchanged)
                    if st.button("📡 요금/정보 가져오기"):
                        raw = self.fetcher.scrape_parking_fee(url)
                        st.session_state["fee_info"] = raw

                    if fee := st.session_state.get("fee_info"):
                        st.write("```")
                        st.write(fee)
                        st.write("```")

                    # ⭐ favourites list
                    favs = get_favorite_list(st.session_state["user_id"])
                    if favs:
                        st.markdown("### ⭐ 내 즐겨찾기")
                        fav_df = pd.DataFrame(favs)[["name", "distance"]]
                        # Add "m" to distance values and reset index to start from 1
                        fav_df["distance"] = fav_df["distance"].astype(str) + " m"
                        fav_df.index = fav_df.index + 1
                        # Rename columns to Korean
                        fav_df = fav_df.rename(columns={"name": "주차장 이름", "distance": "거리"})
                        st.table(fav_df)

                        # reset button
                        if st.button("🗑️ 즐겨찾기 초기화"):
                            clear_favorites(st.session_state["user_id"])
                            st.rerun()
                    else:
                        st.markdown("⭐ 즐겨찾기 없음")

    # ------------------------------------------------------ Main method
    def show(self):
        # Set page config must be the first Streamlit command
        st.set_page_config("🚗 Parking Finder", layout="wide")
        
        # Show different pages based on the current state
        if not st.session_state["is_logged_in"]:
            if st.session_state["page"] == "login":
                self._show_login_page()
            elif st.session_state["page"] == "signup":
                self._show_signup_page()
        else:
            self._show_main_app()


if __name__ == "__main__":
    ParkingApp().show()