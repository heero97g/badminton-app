import streamlit as st
import random
import pandas as pd
import copy

# データの保持
if 'players' not in st.session_state:
    st.session_state.players = []
    st.session_state.match_count = 0
    st.session_state.history = {}
    st.session_state.match_logs = []
    st.session_state.previous_state = None

st.set_page_config(page_title="バド管理Pro", layout="wide")

# --- タイトルとバージョン情報 ---
st.markdown(
    """
    <div style="display: flex; align-items: baseline; gap: 15px;">
        <h2 style="margin: 0; font-size: 2.4rem;">🏸 バドミントン対戦管理</h2>
        <span style="font-size: 0.9rem; color: gray;">ver 1.15 (2026.05.04)</span>
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

def save_state():
    st.session_state.previous_state = {
        'players': copy.deepcopy(st.session_state.players),
        'match_count': st.session_state.match_count,
        'history': copy.deepcopy(st.session_state.history),
        'match_logs': copy.deepcopy(st.session_state.match_logs),
        'current_display': copy.deepcopy(st.session_state.get('current_display')),
        'waiting_list': copy.deepcopy(st.session_state.get('waiting_list'))
    }

# --- サイドバー設定 ---
with st.sidebar:
    st.header("1. 初期設定")
    init_count = st.number_input("開始人数", min_value=4, value=8, step=1)
    if st.button("この人数でリセット"):
        st.session_state.players = [{"id": i+1, "real": 0, "logic": 0, "rest": False, "priority": False} for i in range(int(init_count))]
        st.session_state.match_count = 0
        st.session_state.history = {}
        st.session_state.match_logs = []
        st.session_state.previous_state = None
        if 'current_display' in st.session_state: st.session_state.current_display = None
        if 'waiting_list' in st.session_state: st.session_state.waiting_list = None
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
            st.success(f"ID:{add_id} を追加しました")

# --- メイン画面 ---
if not st.session_state.players:
    st.info("サイドバーから初期人数を設定してください。")
else:
    col_main, col_sub = st.columns([3, 1])

    with col_main:
        st.subheader("対戦カード作成")
        court_num = st.number_input("コート数", min_value=1, value=1)
        
        c1, c2 = st.columns([2, 1])
        with c1:
            gen_button = st.button("🎯 組み合わせ作成", use_container_width=True)
        with c2:
            undo_button = st.button("↩️ 1手戻る", use_container_width=True, disabled=(st.session_state.previous_state is None))

        if undo_button and st.session_state.previous_state:
            prev = st.session_state.previous_state
            st.session_state.players = prev['players']
            st.session_state.match_count = prev['match_count']
            st.session_state.history = prev['history']
            st.session_state.match_logs = prev['match_logs']
            st.session_state.current_display = prev['current_display']
            st.session_state.waiting_list = prev['waiting_list']
            st.session_state.previous_state = None
            st.rerun()

        if gen_button:
            active = [p for p in st.session_state.players if not p['rest']]
            needed = int(court_num * 4)
            
            if len(active) < needed:
                st.error(f"人数不足（現在{len(active)}名）")
            else:
                save_state()
                st.session_state.match_count += 1
                sorted_pool = sorted(active, key=lambda p: (-1000 if p['priority'] else 0) + p['logic'] + random.uniform(0, 0.5))
                selected = sorted_pool[:needed]
                waiting = sorted_pool[needed:]
                
                st.session_state.waiting_list = ", ".join(str(p['id']) for p in waiting)
                
                remaining = selected.copy()
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
                st.rerun()

        # --- 試合表示エリア ---
        # 【修正点】current_display が None でない（中身がある）ときだけ表示するようにガードを入れた
        if st.session_state.get('current_display'):
            st.markdown(f"### 📢 第 {st.session_state.match_count} 試合")
            
            if st.session_state.get('waiting_list'):
                st.warning(f"☕ **待機中:** {st.session_state.waiting_list}")
            else:
                st.info("全員出場中")

            st.write("")
            
            display_matches = st.session_state.current_display
            court_cols = st.columns(len(display_matches))
            for idx, match in enumerate(display_matches):
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
        else:
            # 最初の作成前、またはUndoで初期状態に戻った場合
            st.write("---")
            st.info("「組み合わせ作成」ボタンを押すとこちらに表示されます。")

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
            # ↓ index=False を指定して、左端の数値を表示しないようにする
            st.table(pd.DataFrame(h_data).sort_values("回数", ascending=False), hide_index=True, use_container_width=True)
