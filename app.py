import streamlit as st
import random
import pandas as pd

# データの保持
if 'players' not in st.session_state:
    st.session_state.players = []
    st.session_state.match_count = 0
    st.session_state.history = {}

st.set_page_config(page_title="バド管理Pro", layout="wide")

# --- タイトルとバージョン情報 (サイズ調整済み) ---
st.markdown(
    """
    <div style="display: flex; align-items: baseline; gap: 10px;">
        <h2 style="margin: 0; font-size: 1.5rem;">🏸 バドミントン対戦管理</h2>
        <span style="font-size: 0.8rem; color: gray;">ver 1.6 (2026.05.04)</span>
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
            min_l = min(active_logics) if active_logics else 0
            st.session_state.players.append({"id": int(add_id), "real": 0, "logic": min_l, "rest": False, "priority": True})
            st.success(f"ID:{add_id} を追加しました")

# --- メイン画面 ---
if not st.session_state.players:
    st.info("サイドバーから初期人数を設定して開始してください。")
else:
    col_main, col_sub = st.columns([2, 1])

    with col_main:
        st.subheader("対戦カード作成")
        court_num = st.number_input("コート数", min_value=1, value=1)
        
        if st.button("🎯 組み合わせ作成", use_container_width=True):
            active = [p for p in st.session_state.players if not p['rest']]
            needed = int(court_num * 4)
            
            if len(active) < needed:
                st.error(f"アクティブ人数が足りません（現在{len(active)}名）")
            else:
                st.session_state.match_count += 1
                sorted_for_selection = sorted(active, key=lambda p: (-1000 if p['priority'] else 0) + p['logic'] + random.random())
                selected_pool = sorted_for_selection[:needed]
                waiting = sorted_for_selection[needed:]
                
                remaining = selected_pool.copy()
                random.shuffle(remaining) 
                final_lineup = []
                
                for c in range(int(court_num)):
                    p1 = remaining.pop(0)
                    remaining.sort(key=lambda x: (get_history_count(p1['id'], x['id']) ** 2) + random.random())
                    p2 = remaining.pop(0)
                    p3 = remaining.pop(0)
                    remaining.sort(key=lambda x: (get_history_count(p3['id'], x['id']) ** 2) + random.random())
                    p4 = remaining.pop(0)
                    
                    # 履歴を更新（「今からやる試合」のカウントを先に取得してから更新）
                    c12 = get_history_count(p1['id'], p2['id'])
                    c34 = get_history_count(p3['id'], p4['id'])
                    update_pair_history(p1['id'], p2['id'], p3['id'], p4['id'])
                    
                    final_lineup.append({"court": c+1, "players": [p1, p2, p3, p4], "history": (c12, c34)})
                    
                    for pm in [p1, p2, p3, p4]:
                        for p in st.session_state.players:
                            if p['id'] == pm['id']:
                                p['real'] += 1
                                p['logic'] += 1
                                p['priority'] = False
                
                # 画面表示
                st.markdown(f"### 📢 第 {st.session_state.match_count} 試合")
                for item in final_lineup:
                    p = item["players"]
                    h = item["history"]
                    with st.expander(f"第 {item['court']} コート (ペア履歴: {p[0]['id']}-{p[1]['id']}:{h[0]}回 / {p[2]['id']}-{p[3]['id']}:{h[1]}回)", expanded=True):
                        st.write(f"#### {p[0]['id']} ・ {p[1]['id']}  vs  {p[2]['id']} ・ {p[3]['id']}")
                
                if waiting:
                    st.write("---")
                    st.write(f"**待機中:** {', '.join(str(p['id']) for p in waiting)}")

    with col_sub:
        st.subheader("参加・休止設定")
        for p in st.session_state.players:
            is_active = st.checkbox(f"ID: {p['id']} (計{p['real']}回)", value=not p['rest'], key=f"p_{p['id']}")
            if p['rest'] == is_active:
                p['rest'] = not is_active
                if is_active:
                    active_others = [other['logic'] for other in st.session_state.players if not other['rest'] and other['id'] != p['id']]
                    if active_others: p['logic'] = min(active_others)
                    p['priority'] = True
                    st.toast(f"ID:{p['id']} が復帰しました")

    with st.expander("全ペアの累積履歴一覧"):
        if st.session_state.history:
            h_data = [{"ペア": f"{k[0]}-{k[1]}", "回数": v} for k, v in st.session_state.history.items()]
            st.table(pd.DataFrame(h_data).sort_values("回数", ascending=False))
