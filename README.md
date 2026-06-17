# dApp 배포 체인 추천기

Streamlit + FastAPI + Docker + AWS EC2 기반 추천 웹 애플리케이션
오픈소스소프트웨어실습 기말 대체 과제

내 dApp을 어느 블록체인/L2에 배포할지, 요구사항(6개 지표 가중치)을 입력하면
2026년 실측 지표 기반 점수표로 매칭해 추천해주는 앱입니다.

---

## 주제 선정 배경

2026년 dApp 개발에서 체인 선택은 트랜잭션 볼륨, 사용자 유형, 가스 민감도, 파이널리티 요구에 달려 있습니다.
트렌드를 따라 고르는 것이 아니라, 요구사항에 맞는 체인을 정량적으로 매칭하는 추천 문제입니다.

---

## 아키텍처

```
[사용자] -> [Streamlit 프론트] -> (HTTP POST /recommend) -> [FastAPI 백엔드]
                ^                                                  |
                +------------------ 추천 결과(JSON) ---------------+
```

- front (Streamlit): 입력 슬라이더 / 추천 버튼 / 결과 및 레이더 차트 표시
- back (FastAPI): 가중 점수 계산 후 추천 결과 JSON 반환
- Docker: 프론트/백 컨테이너 분리
- AWS EC2: 실제 서비스 실행 환경

추천 계산은 프론트에서 하지 않고 반드시 FastAPI를 호출해 처리합니다.

---

## 추천 로직

```
score(chain) = sum( user_weight[d] * chain_profile[chain][d] )   (d = 6개 지표)
매칭률(%)    = score / (sum(user_weight[d]) * 10) * 100
```

매칭률 순으로 랭킹하여 1순위, 차순위, 전체 랭킹, 레이더 차트로 출력합니다.

### 평가 지표 6종

| 지표 | 의미 |
|---|---|
| EVM 호환성 | Solidity 자산 재활용 난이도 (zkEVM 타입 기준) |
| 비용 | 트랜잭션 수수료 (저렴할수록 고점) |
| 처리량(TPS) | 실측 균형치 기준 (마케팅 최대치 아님) |
| 파이널리티 | L1 출금 확정 속도 (옵티미스틱 7일 vs ZK 1h) |
| 생태계/유동성 | TVL, 툴링, composability |
| 탈중앙화/보안 | 시퀀서 탈중앙화, 프루프 성숙도 |

### 체인 점수표 - 2026년 실측 기반

| 체인 | EVM | 비용 | TPS | 파이널리티 | 생태계 | 탈중앙화 |
|---|---|---|---|---|---|---|
| Ethereum L1 | 10 | 2 | 2 | 9 | 10 | 10 |
| Arbitrum | 9 | 8 | 6 | 3 | 10 | 8 |
| Base | 9 | 8 | 8 | 3 | 9 | 6 |
| zkSync Era | 6 | 9 | 4 | 8 | 6 | 5 |
| Starknet | 3 | 9 | 5 | 8 | 5 | 5 |
| Solana | 1 | 10 | 10 | 9 | 8 | 6 |
| Cosmos App-chain | 2 | 8 | 8 | 7 | 4 | 6 |

점수 근거 요약

- 비용: L2는 L1 대비 10~100x 저렴, ZK는 EIP-4844 이후 한 자릿수 센트 / Arbitrum ~$0.004 / L1은 가스비 높아 2점
- TPS(실측): Ethereum ~15 / Arbitrum 40~60 / Base 159 / zkSync Era 12~15 / Solana 3,000~4,000
- 파이널리티: 옵티미스틱(Arbitrum/Base) 7일 출금 윈도우(저점) / ZK(zkSync/Starknet) 1시간 내(고점) / Solana 6.4초
- 생태계: Arbitrum/Base가 상위 8개 L2 스테이블코인 유동성의 약 64% 차지
- 탈중앙화: Arbitrum BOLD 무허가 검증(25년 말) / 대부분 ZK는 아직 중앙화 시퀀서


## 디렉토리 구조

```
dapp-chain-recommender/
├── back/
│   ├── main.py
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .dockerignore
├── front/
│   ├── app.py
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .dockerignore
├── docker-compose.yml
├── .gitignore
└── README.md
```
