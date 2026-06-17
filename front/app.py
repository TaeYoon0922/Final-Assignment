import os
import requests
import streamlit as st
import plotly.graph_objects as go

BACKEND_URL = os.environ.get("BACKEND_URL", "http://back:8000")

DIMENSIONS = ["evm", "cost", "tps", "finality", "ecosystem", "decentralization"]

st.set_page_config(page_title="dApp 배포 체인 추천기", page_icon="🔗", layout="centered")

st.title("dApp 배포 체인 추천기")
st.caption(
    "내 dApp을 어느 블록체인/L2에 올릴까? "
    "요구사항을 입력하면 2026년 실측 지표 기반 점수표로 매칭해 추천합니다."
)


@st.cache_data(ttl=300)
def load_meta():
    r = requests.get(f"{BACKEND_URL}/meta", timeout=10)
    r.raise_for_status()
    return r.json()


try:
    meta = load_meta()
except Exception as e:
    st.error(f"백엔드에 연결할 수 없습니다. ({BACKEND_URL})\n\n{e}")
    st.stop()

labels = meta["dimension_labels"]
presets = meta["dapp_presets"]
dapp_types = list(presets.keys())

if "initialized" not in st.session_state:
    st.session_state.dapp_type = dapp_types[0]
    for d, v in presets[dapp_types[0]].items():
        st.session_state[f"w_{d}"] = v
    st.session_state.initialized = True


def apply_preset():
    for d, v in presets[st.session_state.dapp_type].items():
        st.session_state[f"w_{d}"] = v


st.subheader("1. dApp 유형 선택")
st.selectbox(
    "유형을 고르면 아래 가중치가 자동 세팅됩니다 (이후 수동 조정 가능).",
    dapp_types,
    key="dapp_type",
    on_change=apply_preset,
)

st.subheader("2. 우선순위 조정 (0~10)")
st.caption("값이 높을수록 그 지표를 더 중요하게 반영합니다.")

for d in DIMENSIONS:
    st.slider(labels[d], 0, 10, key=f"w_{d}")

st.divider()

if st.button("추천받기", type="primary", use_container_width=True):
    payload = {d: st.session_state[f"w_{d}"] for d in DIMENSIONS}
    payload["dapp_type"] = st.session_state.dapp_type

    try:
        resp = requests.post(f"{BACKEND_URL}/recommend", json=payload, timeout=10)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        st.error(f"추천 요청 실패: {e}")
        st.stop()

    ranked = data["ranked"]
    top = data["top_pick"]

    st.subheader("추천 결과")
    st.success(f"**1순위: {top['chain']}**  ·  매칭률 {top['match']}%  ·  {top['category']}")
    st.write(top["reason"])

    if len(ranked) > 1:
        runner = ranked[1]
        st.info(f"**차순위: {runner['chain']}** ({runner['match']}%) — {runner['reason']}")

    st.markdown("#### 전체 매칭 랭킹")
    st.dataframe(
        [
            {"순위": i + 1, "체인": r["chain"], "분류": r["category"], "매칭률(%)": r["match"]}
            for i, r in enumerate(ranked)
        ],
        hide_index=True,
        use_container_width=True,
    )

    st.markdown("#### 상위 3개 체인 지표 비교")
    axis_labels = [labels[d] for d in DIMENSIONS] + [labels[DIMENSIONS[0]]]
    fig = go.Figure()
    for r in ranked[:3]:
        vals = [r["profile"][d] for d in DIMENSIONS]
        vals.append(vals[0])
        fig.add_trace(go.Scatterpolar(r=vals, theta=axis_labels, fill="toself", name=r["chain"]))
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 10])),
        showlegend=True,
        height=450,
    )
    st.plotly_chart(fig, use_container_width=True)

    with st.expander("입력한 가중치 보기"):
        st.json(data["weights"])

st.divider()
st.caption(
    "점수는 2026년 실측 지표(수수료·실측 TPS·출금 파이널리티·TVL 등)를 0~10으로 정규화한 값입니다. "
    "교육용 데모이며 실제 배포 결정은 최신 L2Beat·DefiLlama 데이터로 검증하세요."
)
