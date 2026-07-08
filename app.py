import streamlit as st
import json
import os
import uuid
from datetime import datetime

DATA_FILE = "todos.json"
CATEGORIES = ["업무", "개인", "공부"]
CATEGORY_STYLES = {
    "업무": ("#e0edff", "#1d4ed8"),
    "개인": ("#e6f7ec", "#15803d"),
    "공부": ("#f3e8ff", "#7e22ce"),
}
AUTO_OPTION = "자동분류"
DEFAULT_CATEGORY = "개인"
CATEGORY_KEYWORDS = {
    "업무": [
        "회의", "미팅", "보고서", "업무", "프로젝트", "발표", "이메일", "메일",
        "클라이언트", "계약", "출근", "퇴근", "회사", "리포트", "야근", "결재",
        "기획", "고객", "영업", "제출", "회식",
    ],
    "공부": [
        "공부", "시험", "과제", "강의", "수업", "독서", "학교", "자격증",
        "논문", "숙제", "복습", "예습", "토익", "영어", "수학", "책",
    ],
    "개인": [
        "쇼핑", "청소", "빨래", "운동", "병원", "약속", "가족", "친구",
        "여행", "취미", "장보기", "요리", "은행", "약국", "미용실", "산책",
        "밥", "식사",
    ],
}


def classify_category(title):
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(keyword in title for keyword in keywords):
            return category
    return None

st.set_page_config(page_title="심플투두", page_icon="📝", layout="centered")


def load_todos():
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError):
        return []


def save_todos(todos):
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(todos, f, ensure_ascii=False, indent=2)
    except OSError as e:
        st.error(f"할일 저장에 실패했습니다: {e}")


if "todos" not in st.session_state:
    st.session_state.todos = load_todos()
if "editing_id" not in st.session_state:
    st.session_state.editing_id = None
if "filter" not in st.session_state:
    st.session_state.filter = "전체"


def add_todo(title, category):
    title = title.strip()
    if not title:
        return
    st.session_state.todos.append({
        "id": str(uuid.uuid4()),
        "title": title,
        "category": category,
        "completed": False,
        "createdAt": datetime.now().isoformat(),
    })
    save_todos(st.session_state.todos)


def delete_todo(todo_id):
    st.session_state.todos = [t for t in st.session_state.todos if t["id"] != todo_id]
    if st.session_state.editing_id == todo_id:
        st.session_state.editing_id = None
    save_todos(st.session_state.todos)


def toggle_todo(todo_id):
    for t in st.session_state.todos:
        if t["id"] == todo_id:
            t["completed"] = not t["completed"]
            break
    save_todos(st.session_state.todos)


def save_edit(todo_id, new_title, new_category):
    new_title = new_title.strip()
    if not new_title:
        return
    for t in st.session_state.todos:
        if t["id"] == todo_id:
            t["title"] = new_title
            t["category"] = new_category
            break
    st.session_state.editing_id = None
    save_todos(st.session_state.todos)


def category_badge(category):
    bg, color = CATEGORY_STYLES.get(category, ("#eee", "#555"))
    return (
        f'<span style="background:{bg};color:{color};padding:3px 10px;'
        f'border-radius:999px;font-size:12.5px;white-space:nowrap;">{category}</span>'
    )


st.title("📝 심플투두")

with st.form("add_form", clear_on_submit=True):
    col_input, col_category, col_submit = st.columns([3, 1, 1])
    title_input = col_input.text_input(
        "할일", placeholder="할일을 입력하세요", label_visibility="collapsed"
    )
    category_input = col_category.selectbox(
        "카테고리", [AUTO_OPTION] + CATEGORIES, index=0, label_visibility="collapsed"
    )
    submitted = col_submit.form_submit_button("추가", use_container_width=True)
    if submitted and title_input.strip():
        if category_input == AUTO_OPTION:
            resolved_category = classify_category(title_input) or DEFAULT_CATEGORY
            st.toast(f"'{resolved_category}' 카테고리로 자동 분류되었습니다.")
        else:
            resolved_category = category_input
        add_todo(title_input, resolved_category)

st.session_state.filter = st.radio(
    "필터",
    ["전체"] + CATEGORIES,
    horizontal=True,
    index=(["전체"] + CATEGORIES).index(st.session_state.filter),
    label_visibility="collapsed",
)

todos = st.session_state.todos
current_filter = st.session_state.filter
filtered = todos if current_filter == "전체" else [t for t in todos if t["category"] == current_filter]

total = len(filtered)
done = sum(1 for t in filtered if t["completed"])
percent = int(done / total * 100) if total else 0

st.progress(percent / 100)
st.caption(f"{current_filter} 진행률: {done}/{total} 완료 ({percent}%)")

st.divider()

if not filtered:
    st.info("표시할 할일이 없습니다.")

for todo in filtered:
    if st.session_state.editing_id == todo["id"]:
        col_title, col_category, col_save, col_cancel = st.columns([3, 1.2, 1, 1])
        new_title = col_title.text_input(
            "제목", value=todo["title"], key=f"edit_title_{todo['id']}",
            label_visibility="collapsed",
        )
        new_category = col_category.selectbox(
            "카테고리", CATEGORIES, index=CATEGORIES.index(todo["category"]),
            key=f"edit_cat_{todo['id']}", label_visibility="collapsed",
        )
        if col_save.button("저장", key=f"save_{todo['id']}", use_container_width=True):
            save_edit(todo["id"], new_title, new_category)
            st.rerun()
        if col_cancel.button("취소", key=f"cancel_{todo['id']}", use_container_width=True):
            st.session_state.editing_id = None
            st.rerun()
    else:
        col_check, col_badge, col_title, col_edit, col_delete = st.columns(
            [0.6, 1, 3, 1, 1]
        )
        checked = col_check.checkbox(
            "완료", value=todo["completed"], key=f"chk_{todo['id']}",
            label_visibility="collapsed",
        )
        if checked != todo["completed"]:
            toggle_todo(todo["id"])
            st.rerun()

        col_badge.markdown(category_badge(todo["category"]), unsafe_allow_html=True)

        title_text = f"~~{todo['title']}~~" if todo["completed"] else todo["title"]
        col_title.markdown(title_text)

        if col_edit.button("수정", key=f"edit_{todo['id']}", use_container_width=True):
            st.session_state.editing_id = todo["id"]
            st.rerun()
        if col_delete.button("삭제", key=f"del_{todo['id']}", use_container_width=True):
            delete_todo(todo["id"])
            st.rerun()
