import streamlit as st
import random
import pandas as pd

# データの保持
if 'players' not in st.session_state:
    st.session_state.players = []
    st.session_state.match_count = 0

st.set_page_config(page_title="バド管理Pro", layout="wide")
st.title("🏸 バドミントン対戦管理")

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
        st.success(f"{init_count}人で開始します")

    st.divider()
    st.header("2. メンバー追加")
    # マイナス入力を防ぎ、次のIDを自動提示
    next_id_val = max([p['id'] for p in st.session_state.players]) + 1 if st.session_state.players else 1
    add_id = st.number_input("追加プレイヤーID", min_value=1, value=int(next_id_val))
    
    if st.button("プレイヤーを追加"):
        if any(p['id'] == add_id for p in st.session_state.players):
            st.error("そのIDは既に存在します")
        else:
            # 復帰時と同様、現在の最小試合数を引き継ぐ
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
            # 休止中（rest=True）を除外したアクティブメンバー
            active = [p for p in st.session_state.players if not p['rest']]
            needed = int(court_num * 4)
            
            if len(active) < needed:
                st.error(f"アクティブ人数が足りません（現在{len(active)}名 / 必要{needed}名）\n休止設定を確認してください。")
            else:
                st.session_state.match_count += 1
                # 優先・試合数・乱数でソート
                sorted_list = sorted(active, key=lambda p: (-1000 if p['priority'] else 0) + p['logic'] + random.random())
                selected = sorted_list[:needed]
                waiting = sorted_list[needed:]
                
                st.markdown(f"### 📢 第 {st.session_state.match_count} 試合")
                
                # コートごとの表示
                for i in range(int(court_num)):
                    base = i * 4
                    p1, p2, p3, p4 = selected[base:base+4]
                    with st.expander(f"第 {i+1} コート", expanded=True):
                        st.write(f"#### {p1['id']} ・ {p2['id']}  vs  {p3['id']} ・ {p4['id']}")
                    
                    # 試合数と優先権の更新
                    for p_data in (p1, p2, p3, p4):
                        for p in st.session_state.players:
                            if p['id'] == p_data['id']:
                                p['real'] += 1
                                p['logic'] += 1
                                p['priority'] = False
                
                if waiting:
                    st.write("---")
                    st.write(f"**待機中:** {', '.join(str(p['id']) for p in waiting)}")

    with col_sub:
        st.subheader("休止・復帰")
        st.caption("チェックを外すと試合から除外されます")
        
        for p in st.session_state.players:
            # 前回の状態を保持しつつ、その場で更新
            # 「参加中」というラベルでチェックボックスを作成
            is_active = st.checkbox(f"ID: {p['id']} (計{p['real']}回)", value=not p['rest'], key=f"p_{p['id']}")
            
            # チェックボックスの状態をデータに反映
            if p['rest'] == is_active: # 状態が反転していたら更新
                p['rest'] = not is_active
                if is_active: # 復帰した瞬間の処理
                    active_others = [other['logic'] for other in st.session_state.players if not other['rest'] and other['id'] != p['id']]
                    if active_others:
                        p['logic'] = min(active_others)
                    p['priority'] = True
                    st.toast(f"ID:{p['id']} が復帰しました（次戦優先）")

    # データ一覧（デバッグ・確認用）
    with st.expander("全データ確認"):
        st.table(pd.DataFrame(st.session_state.players))