import streamlit as st
import random
import pandas as pd

# データの保持
if 'players' not in st.session_state:
    st.session_state.players = []
    st.session_state.match_count = 0
    # 誰と誰が同じコートになったかの履歴 {(id1, id2): 回数}
    st.session_state.history = {}

st.set_page_config(page_title="バド管理Pro", layout="wide")
st.markdown(
    """
    <div style="display: flex; align-items: baseline;">
        <h1 style="margin-right: 15px;">🏸 バドミントン対戦管理</h1>
        <span style="font-size: 0.8rem; color: gray;">ver 1.2 (2026.05.04)</span>
    </div>
    """, 
    unsafe_allow_html=True
)
# --- 便利関数 ---
def get_history_count(id1, id2):
    """二人の過去の対戦・ペア履歴回数を取得（順序不問）"""
    pair = tuple(sorted((id1, id2)))
    return st.session_state.history.get(pair, 0)

def update_history(player_ids):
    """同じコートにいた4名全員の組み合わせ履歴を更新"""
    from itertools import combinations
    for p1, p2 in combinations(player_ids, 2):
        pair = tuple(sorted((p1, p2)))
        st.session_state.history[pair] = st.session_state.history.get(pair, 0) + 1

# --- サイドバー設定 ---
with st.sidebar:
    st.header("1. 初期設定")
    init_count = st.number_input("開始人数", min_value=4, value=8, step=1)
    if st.button("この人数でリセット"):
        st.session_state.players = [
            {"id": i+1, "real": 0, "logic": 0, "rest": False, "priority": False} 
            for i in range(int(init_count))
        ]
        st.session_state.match_count = 0
        st.session_state.history = {}
        st.success(f"{init_count}人で開始します")

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
                
                # 1. 試合数に基づき、今回出場するメンバーを選出（ここは変更なし）
                sorted_for_selection = sorted(active, key=lambda p: (-1000 if p['priority'] else 0) + p['logic'] + random.random())
                selected_pool = sorted_for_selection[:needed]
                waiting = sorted_for_selection[needed:]
                
                remaining = selected_pool.copy()
                random.shuffle(remaining) # 最初に混ぜることで固定化を防ぐ
                final_lineup = []
                
                for c in range(int(court_num)):
                    # コートの1人目を決定
                    p1 = remaining.pop(0)
                    
                    # 2人目（ペア）の選出：過去にp1と「ペア」になった回数を最優先で評価
                    # get_history_count は対戦も含んでいるため、ペア専用の判定を入れるのが理想的ですが
                    # 4人の場合は「同じコートになった回数」を避けるだけで全3パターンが均等に出やすくなります
                    remaining.sort(key=lambda x: get_history_count(p1['id'], x['id']) + random.random())
                    p2 = remaining.pop(0)
                    
                    # 3人目・4人目の選出
                    p3 = remaining.pop(0)
                    remaining.sort(key=lambda x: get_history_count(p3['id'], x['id']) + random.random())
                    p4 = remaining.pop(0)
                    
                    court_members = [p1, p2, p3, p4]
                    final_lineup.append(court_members)
                    
                    # 履歴更新
                    update_history([p['id'] for p in court_members])
                    
                    # 試合数と優先権の更新
                    for pm in court_members:
                        for p in st.session_state.players:
                            if p['id'] == pm['id']:
                                p['real'] += 1
                                p['logic'] += 1
                                p['priority'] = False
                                
                st.markdown(f"### 📢 第 {st.session_state.match_count} 試合")
                for i, court in enumerate(final_lineup):
                    with st.expander(f"第 {i+1} コート", expanded=True):
                        st.write(f"#### {court[0]['id']} ・ {court[1]['id']}  vs  {court[2]['id']} ・ {court[3]['id']}")
                
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

    with st.expander("対戦・ペア重複カウント（確認用）"):
        if st.session_state.history:
            h_data = [{"ペア": f"{k[0]}-{k[1]}", "回数": v} for k, v in st.session_state.history.items()]
            st.table(pd.DataFrame(h_data).sort_values("回数", ascending=False))
