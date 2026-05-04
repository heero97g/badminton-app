import streamlit as st
import random
import pandas as pd

# データの保持
if 'players' not in st.session_state:
    st.session_state.players = []
    st.session_state.match_count = 0
    st.session_state.history = {}
    st.session_state.match_logs = []

st.set_page_config(page_title="バド管理Pro", layout="wide")

# --- タイトルとバージョン情報 ---
st.markdown(
    """
    <div style="display: flex; align-items: baseline; gap: 15px;">
        <h2 style="margin: 0; font-size: 2.4rem;">🏸 バドミントン対戦管理</h2>
        <span style="font-size: 0.9rem; color: gray;">ver 1.12 (2026.05.04)</span>
    </div>
    <br>
    """, 
    unsafe_allow_html=True
)

# --- 便利関数 ---
def get_history_count(id1, id2):
    pair = tuple(sorted((id1, id2)))
    return st.session_state.history.get(pair, 0)

def update_pair_history(p1, p2, p3, p4):
    for a, b in [(p1, p2), (p3, p4)]:
        pair = tuple(sorted((a, b)))
        st.session_state.history[pair] = st.session_state.history.get(pair, 0) + 1

# --- サイドバー設定 ---
with st.sidebar:
    st.header("1. 初期設定")
    init_count = st.number_input("開始人数", min_value=4, value=8, step=1)
    if st.button("この人数でリセット"):
        st.session_state.players = [{"id": i+1, "real": 0, "logic": 0, "rest": False, "priority": False} for i in range(int(init_count))]
        st.session_state.match_count = 0
        st.session_state.history = {}
        st.session_state.match_logs = []
        if 'current_display' in st.session_state: del st.session_state.current_display
        st.rerun()

    st.divider()
    st.header("2. メンバー追加")
    next_id_val = max([p['id'] for p in st.session_state.players]) + 1 if st.session_state.players else 1
    add_id = st.number_input("追加プレイヤーID", min_value=1, value=int(next_id_val))
    
    if st.button("プレイヤーを追加"):
        if any(p['id'] == add_id for p in st.session_state.players):
            st.error("そのIDは既に存在します")
        else:
            active_logics = [p['logic'] for p in st.session_state.players if not p['rest']]
            avg_l = sum(active_logics) / len(active_logics) if active_logics else 0
            st.session_state.players.append({"id": int(add_id), "real": 0, "logic": avg_l, "rest": False, "priority": True})
            st.success(f"ID:{add_id} を追加しました(初回優先)")

# --- メイン画面 ---
if not st.session_state.players:
    st.info("サイドバーから初期人数を設定してください。")
else:
    col_main, col_sub = st.columns([3, 1])

    with col_main:
        st.subheader("対戦カード作成")
        # 【修正点】初期値を1に固定し、自動で変動しないように変更
        court_num = st.number_input("コート数", min_value=1, value=1)
        
        if st.button("🎯 組み合わせ作成", use_container_width=True):
            active = [p for p in st.session_state.players if not p['rest']]
            needed = int(court_num * 4)
            
            if len(active) < needed:
                st.error(f"人数不足（現在{len(active)}名 / 必要{needed}名）")
            else:
                st.session_state.match_count += 1
                sorted_pool = sorted(active, key=lambda p: (-1000 if p['priority'] else 0) + p['logic'] + random.uniform(0, 0.5))[:needed]
                
                remaining = sorted_pool.copy()
                random.shuffle(remaining)
                current_matches = []
                
                for c in range(int(court_num)):
                    p1 = remaining.pop(0)
                    remaining.sort(key=lambda x: (get_history_count(p1['id'], x['id']) ** 2) + random.random())
                    p2 = remaining.pop(0)
                    p3 = remaining.pop(0)
                    remaining.sort(key=lambda x: (get_history_count(p3['id'], x['id']) ** 2) + random.random())
                    p4 = remaining.pop(0)
                    
                    match_data = {
                        "game_no": st.session_state.match_count,
                        "court": c + 1,
                        "pair_a": (p1['id'], p2['id']),
                        "pair_b": (p3['id'], p4['id']),
                        "members": {p1['id'], p2['id'], p3['id'], p4['id']}
                    }
                    current_matches.append(match_data)
                    st.session_state.match_logs.append(match_data)
                    update_pair_history(p1['id'], p2['id'], p3['id'], p4['id'])
                    
                    for pm in [p1, p2, p3, p4]:
                        for p in st.session_state.players:
                            if p['id'] == pm['id']:
                                p['real'] += 1
                                p['logic'] += 1
                                p['priority'] = False
                
                st.session_state.current_display = current_matches

        # --- 試合表示エリア ---
        if 'current_display' in st.session_state:
            st.markdown(f"### 📢 第 {st.session_state.match_count} 試合")
            court_cols = st.columns(len(st.session_state.current_display))
            for idx, match in enumerate(st.session_state.current_display):
                with court_cols[idx]:
                    p_a, p_b = match["pair_a"], match["pair_b"]
                    current_members = match["members"]
                    past = [m for m in st.session_state.match_logs if m["members"] == current_members and m["game_no"] < st.session_state.match_count]
                    with st.container(border=True):
                        st.markdown(f"**第 {match['court']} コート**")
                        st.markdown(f"### {p_a[0]}・{p_a[1]}\n### vs\n### {p_b[0]}・{p_b[1]}")
                        with st.expander("過去履歴"):
                            if past:
                                for pm in reversed(past): st.caption(f"第{pm['game_no']}試合: ({pm['pair_a'][0]}-{pm['pair_a'][1]}) vs ({pm['pair_b'][0]}-{pm['pair_b'][1]})")
                            else: st.caption("初めての組み合わせです")

    with col_sub:
        st.subheader("参加状況")
        for p in st.session_state.players:
            label = f"ID:{p['id']} ({p['real']}回)" + (" ★" if p['priority'] else "")
            is_active = st.checkbox(label, value=not p['rest'], key=f"p_{p['id']}")
            if p['rest'] == is_active:
                p['rest'] = not is_active
                if is_active:
                    active_others = [other['logic'] for other in st.session_state.players if not other['rest'] and other['id'] != p['id']]
                    if active_others:
                        p['logic'] = sum(active_others) / len(active_others)
                    p['priority'] = True
                    st.toast(f"ID:{p['id']} が復帰しました")
                st.rerun()

    with st.expander("全ペアの累積履歴一覧"):
        if st.session_state.history:
            h_data = [{"ペア": f"{k[0]}-{k[1]}", "回数": v} for k, v in st.session_state.history.items()]
            st.table(pd.DataFrame(h_data).sort_values("回数", ascending=False))
