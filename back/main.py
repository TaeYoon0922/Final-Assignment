from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

app = FastAPI(title="dApp Chain Recommender API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DIMENSIONS = ["evm", "cost", "tps", "finality", "ecosystem", "decentralization"]

DIMENSION_LABELS = {
    "evm": "EVM 호환성",
    "cost": "비용(저렴함)",
    "tps": "처리량(TPS)",
    "finality": "파이널리티",
    "ecosystem": "생태계/유동성",
    "decentralization": "탈중앙화/보안",
}

CHAIN_PROFILE = {
    "Ethereum L1":      {"evm": 10, "cost": 2,  "tps": 2,  "finality": 9, "ecosystem": 10, "decentralization": 10},
    "Arbitrum":         {"evm": 9,  "cost": 8,  "tps": 6,  "finality": 3, "ecosystem": 10, "decentralization": 8},
    "Base":             {"evm": 9,  "cost": 8,  "tps": 8,  "finality": 3, "ecosystem": 9,  "decentralization": 6},
    "zkSync Era":       {"evm": 6,  "cost": 9,  "tps": 4,  "finality": 8, "ecosystem": 6,  "decentralization": 5},
    "Starknet":         {"evm": 3,  "cost": 9,  "tps": 5,  "finality": 8, "ecosystem": 5,  "decentralization": 5},
    "Solana":           {"evm": 1,  "cost": 10, "tps": 10, "finality": 9, "ecosystem": 8,  "decentralization": 6},
    "Cosmos App-chain": {"evm": 2,  "cost": 8,  "tps": 8,  "finality": 7, "ecosystem": 4,  "decentralization": 6},
}

CHAIN_META = {
    "Ethereum L1":      {"category": "L1 세틀먼트", "note": "최고 수준의 보안·생태계. 다만 가스비가 높아 고액 정산용."},
    "Arbitrum":         {"category": "Optimistic Rollup", "note": "DeFi TVL 1위, 평균 수수료 ~$0.004. 복잡한 DeFi의 사실상 기본값."},
    "Base":             {"category": "Optimistic Rollup", "note": "코인베이스 기반 소비자 dApp 진입점. 실측 159 TPS로 고성장."},
    "zkSync Era":       {"category": "ZK Rollup (Type 4)", "note": "낮은 수수료 + 1시간 내 출금 확정. 증명 오버헤드로 TPS는 보수적."},
    "Starknet":         {"category": "ZK Rollup (Cairo VM)", "note": "계정 추상화 네이티브. 커스텀 VM이라 EVM 자산 재활용은 어려움."},
    "Solana":           {"category": "비EVM L1", "note": "지속 3,000~4,000 TPS, 6.4초 파이널리티. 게임·소비자 앱 강자(Rust)."},
    "Cosmos App-chain": {"category": "주권형 App-chain", "note": "Cosmos SDK 기반. 수수료·거버넌스 완전 제어. 생태계는 분산적."},
}

DAPP_TYPE_PRESETS = {
    "DeFi 프로토콜":   {"evm": 8, "cost": 6, "tps": 5, "finality": 6, "ecosystem": 10, "decentralization": 7},
    "소비자 앱":       {"evm": 6, "cost": 9, "tps": 9, "finality": 4, "ecosystem": 7,  "decentralization": 4},
    "게임":            {"evm": 4, "cost": 9, "tps": 10, "finality": 3, "ecosystem": 5,  "decentralization": 4},
    "결제/정산":       {"evm": 5, "cost": 8, "tps": 7, "finality": 10, "ecosystem": 6,  "decentralization": 8},
    "NFT/거버넌스":    {"evm": 8, "cost": 7, "tps": 5, "finality": 5, "ecosystem": 8,  "decentralization": 7},
}


class RecommendRequest(BaseModel):
    evm: int = Field(5, ge=0, le=10)
    cost: int = Field(5, ge=0, le=10)
    tps: int = Field(5, ge=0, le=10)
    finality: int = Field(5, ge=0, le=10)
    ecosystem: int = Field(5, ge=0, le=10)
    decentralization: int = Field(5, ge=0, le=10)
    dapp_type: str | None = None


def build_reason(chain: str, weighted: dict) -> str:
    top2 = sorted(DIMENSIONS, key=lambda d: weighted[d], reverse=True)[:2]
    labels = " / ".join(DIMENSION_LABELS[d] for d in top2)
    return f"{labels} 측면에서 요구사항과 잘 맞음 — {CHAIN_META[chain]['note']}"


@app.get("/")
def root():
    return {"service": "dApp Chain Recommender API", "status": "ok"}


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.get("/meta")
def meta():
    return {
        "dimensions": DIMENSIONS,
        "dimension_labels": DIMENSION_LABELS,
        "dapp_presets": DAPP_TYPE_PRESETS,
        "chain_profile": CHAIN_PROFILE,
        "chain_meta": CHAIN_META,
    }


@app.post("/recommend")
def recommend(req: RecommendRequest):
    weights = {d: getattr(req, d) for d in DIMENSIONS}
    max_raw = sum(weights[d] * 10 for d in DIMENSIONS) or 1

    ranked = []
    for chain, profile in CHAIN_PROFILE.items():
        weighted = {d: weights[d] * profile[d] for d in DIMENSIONS}
        raw = sum(weighted.values())
        match = round(raw / max_raw * 100, 1)
        ranked.append({
            "chain": chain,
            "category": CHAIN_META[chain]["category"],
            "match": match,
            "profile": profile,
            "weighted": weighted,
            "reason": build_reason(chain, weighted),
        })

    ranked.sort(key=lambda x: x["match"], reverse=True)

    return {
        "weights": weights,
        "dapp_type": req.dapp_type,
        "dimension_labels": DIMENSION_LABELS,
        "ranked": ranked,
        "top_pick": ranked[0],
    }
