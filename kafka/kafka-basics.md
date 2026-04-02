# Apache Kafka 기본 개념 및 동작 원리

## Kafka란?

LinkedIn에서 개발하고 Apache 재단에 오픈소스로 기증한 **분산 이벤트 스트리밍 플랫폼**.

단순한 메시지 큐가 아니라, 대규모 실시간 데이터 흐름을 처리하는 **데이터 허브** 역할을 한다.

---

## 왜 Kafka를 사용하는가?

### 문제 상황: 서비스가 많아질수록 연결이 복잡해진다

서비스가 여러 개 있고, 서로 데이터를 주고받아야 함.

```
[주문 서비스] → [결제 서비스]
[주문 서비스] → [재고 서비스]
[주문 서비스] → [알림 서비스]
[주문 서비스] → [분석 서비스]
```

직접 연결(HTTP 호출 등)하면:
- 상대 서비스가 죽어 있으면 요청도 실패 → 강한 결합(Coupling)
- 서비스가 늘어날수록 연결 수가 폭발적으로 증가
- 데이터를 한 번에 여러 곳에 보내려면 코드가 복잡해짐

### Kafka로 해결

```
[주문 서비스] → Kafka(order-events topic)
                        ↓
          ┌─────────────┼─────────────┐
     [결제 서비스]  [재고 서비스]  [알림 서비스]  [분석 서비스]
```

- 주문 서비스는 Kafka에 메시지만 보내면 끝 → **느슨한 결합(Decoupling)**
- 각 서비스는 Kafka에서 독립적으로 읽음 → 한 서비스가 죽어도 나머지 영향 없음
- 새 서비스가 추가돼도 주문 서비스 코드는 변경할 필요 없음

### Kafka의 핵심 장점 요약

| 장점 | 설명 |
|------|------|
| **높은 처리량** | 초당 수백만 건의 메시지도 처리 가능 |
| **낮은 지연** | 디스크 순차 I/O로 빠른 저장/읽기 |
| **내결함성** | Replication으로 서버 장애에도 데이터 유실 없음 |
| **확장성** | Broker/Partition 추가로 수평 확장 가능 |
| **메시지 보존** | 읽어도 삭제 안 함 → 재처리, 여러 소비자 가능 |
| **순서 보장** | Partition 내에서 순서 보장 |
| **느슨한 결합** | Producer와 Consumer가 서로를 몰라도 됨 |

---

## 핵심 구성 요소

### 전체 구조

```
Producer
  │
  │  메시지 전송
  ▼
[Broker Cluster]
  ├── Topic: order-events
  │     ├── Partition 0: [msg0][msg1][msg2]...
  │     ├── Partition 1: [msg0][msg1][msg2]...
  │     └── Partition 2: [msg0][msg1][msg2]...
  └── Topic: payment-events
        └── Partition 0: [msg0][msg1]...
              │
              │  메시지 읽기
              ▼
         Consumer Group
           ├── Consumer 1 (Partition 0 담당)
           ├── Consumer 2 (Partition 1 담당)
           └── Consumer 3 (Partition 2 담당)
```

---

### Producer (생산자)

- 메시지를 Kafka에 **보내는** 쪽
- 어떤 Topic에 보낼지 지정
- 메시지에 **Key**를 붙일 수 있음 → Key가 같으면 항상 같은 Partition으로 전송
  - 예: 같은 유저의 이벤트를 항상 같은 Partition에 → 유저 단위 순서 보장
- Key가 없으면 라운드로빈으로 Partition에 분배

```
// Key 있는 경우: userId를 Key로 사용
producer.send("order-events", userId, orderMessage)
→ hash(userId) % partitionCount = 항상 같은 Partition

// Key 없는 경우
producer.send("order-events", null, orderMessage)
→ Partition 0, 1, 2, 0, 1, 2, ... 순서로 분배
```

---

### Consumer (소비자)

- 메시지를 Kafka에서 **읽는** 쪽
- **Consumer Group** 단위로 묶여서 동작
- 읽은 위치(Offset)를 커밋하여 어디까지 읽었는지 추적

---

### Broker

- Kafka 서버 인스턴스 하나
- 메시지를 **디스크에 저장**하고 Producer/Consumer에게 서비스 제공
- 여러 Broker가 모이면 **Cluster**를 구성
- Cluster 내 각 Broker는 일부 Partition의 **Leader** 역할을 맡음

```
Cluster (Broker 3대)
├── Broker 1: order-events Partition 0 Leader, payment-events Partition 1 Follower
├── Broker 2: order-events Partition 1 Leader, order-events Partition 0 Follower
└── Broker 3: order-events Partition 2 Leader, order-events Partition 1 Follower
```

---

### Topic

- 메시지를 분류하는 **논리적 단위**
- 쉽게 말하면: "이 종류의 메시지들은 여기 넣어" 하는 **채널/카테고리**
- 하나의 Topic은 여러 **Partition**으로 나뉨

---

### Partition

- Topic의 **물리적 분할 단위**
- 각 Partition은 **순서가 보장된 메시지 로그** (append-only)
- Partition이 많을수록 **병렬 처리 가능** → 처리량 증가

```
Topic: order-events (Partition 3개)

Partition 0: [order#1] [order#4] [order#7] ...  → offset 0, 1, 2 ...
Partition 1: [order#2] [order#5] [order#8] ...  → offset 0, 1, 2 ...
Partition 2: [order#3] [order#6] [order#9] ...  → offset 0, 1, 2 ...
```

> 주의: **전체 Topic에서의 순서는 보장되지 않음**. Partition 내에서만 순서 보장.
> 전체 순서가 필요하면 Partition을 1개로 설정 (대신 병렬 처리 불가).

---

### Offset

- Partition 내 각 메시지에 붙는 **순서 번호** (0부터 시작)
- Consumer가 어디까지 읽었는지 추적하는 **책갈피** 역할
- Consumer가 offset을 **커밋(commit)** 하면, 재시작해도 이어서 읽을 수 있음

```
Partition 0:
  offset 0: order#1
  offset 1: order#4
  offset 2: order#7  ← Consumer가 여기까지 읽고 커밋
  offset 3: order#9  ← 다음번에 여기서 이어서 시작
```

---

## Consumer Group

Consumer Group은 Kafka에서 가장 중요한 개념 중 하나다.

### 기본 개념

**Consumer Group = 하나의 애플리케이션을 여러 인스턴스로 실행하는 단위**

같은 Group에 속한 Consumer들은 **Topic의 Partition을 나눠서** 읽는다.
즉, 같은 메시지를 중복으로 처리하지 않고, **팀으로 나눠서 병렬 처리**하는 것.

### 실제 시나리오

**상황**: `order-events` Topic에 메시지가 초당 1000개 들어오는데, Consumer 1개로는 처리가 벅차다.

**해결**: Consumer를 늘려서 병렬 처리한다.

```
Topic: order-events (Partition 3개)

[초기 상태] Consumer Group "order-processor" (Consumer 1개)
  Consumer 1 → Partition 0, 1, 2 모두 처리 (버거움)

[스케일아웃] Consumer 3개로 늘림
  Consumer 1 → Partition 0만 처리
  Consumer 2 → Partition 1만 처리
  Consumer 3 → Partition 2만 처리
  → 처리량 3배!
```

### Consumer 수와 Partition 수의 관계

```
Case 1: Consumer 수 = Partition 수 (이상적)
  Partition 0 → Consumer 1
  Partition 1 → Consumer 2
  Partition 2 → Consumer 3

Case 2: Consumer 수 < Partition 수
  Partition 0 → Consumer 1  (Consumer 1이 두 개 담당)
  Partition 1 → Consumer 1
  Partition 2 → Consumer 2

Case 3: Consumer 수 > Partition 수 (낭비)
  Partition 0 → Consumer 1
  Partition 1 → Consumer 2
  Consumer 3 → 대기 (아무것도 못 읽음)
```

> **핵심**: 병렬 처리의 최대 단위는 **Partition 수**다.
> Consumer를 아무리 늘려도 Partition 수 이상으로는 병렬화되지 않음.

### 여러 Consumer Group이 같은 Topic을 읽을 때

각 Consumer Group은 **완전히 독립적으로** 읽는다.
같은 메시지를 각 Group이 따로 처음부터 읽을 수 있다.

```
Topic: order-events

Consumer Group "order-processor" (주문 처리 서비스)
  → 주문 처리 로직 수행
  → Partition 0 offset 150까지 읽은 상태

Consumer Group "analytics-service" (분석 서비스)
  → 분석용 데이터 집계
  → Partition 0 offset 89까지 읽은 상태

Consumer Group "notification-service" (알림 서비스)
  → 유저에게 푸시 알림 전송
  → Partition 0 offset 150까지 읽은 상태
```

→ 한 서비스가 느려도, 죽어도 다른 서비스에 영향 없음.
→ 새 서비스가 생기면 새 Group으로 등록하면 됨. **Producer 코드 수정 불필요**.

### Rebalancing (리밸런싱)

Consumer가 추가되거나 죽으면 Partition 할당을 재조정하는 과정.

```
[정상 상태]
Consumer 1 → Partition 0
Consumer 2 → Partition 1
Consumer 3 → Partition 2

[Consumer 2 갑자기 죽음]
→ Rebalancing 발생!
Consumer 1 → Partition 0, 1
Consumer 3 → Partition 2

[Consumer 4 추가]
→ Rebalancing 발생!
Consumer 1 → Partition 0
Consumer 3 → Partition 1
Consumer 4 → Partition 2
```

리밸런싱 중에는 **잠깐 소비가 멈춤** (Stop the World). 너무 자주 일어나면 성능에 영향을 줄 수 있다.

---

## Topic 분류의 장점과 기준

### Topic 분류가 왜 필요한가?

Topic 없이 모든 메시지를 한 곳에 쌓으면:
- "이 메시지가 주문인지, 결제인지, 로그인지" 모름
- 관련 없는 서비스까지 전체 메시지를 다 읽어야 함
- 각기 다른 보존 기간/보안 설정 불가

Topic으로 분류하면:
- Consumer가 필요한 Topic만 구독 → 불필요한 데이터 처리 없음
- Topic별로 다른 설정 적용 가능 (보존 기간, Partition 수, 복제 수 등)
- 어떤 데이터가 흐르는지 한눈에 파악 가능 (카탈로그처럼)

### Topic 분류 기준

**기준 1: 도메인/이벤트 유형별**

가장 일반적인 방법. 어떤 일이 일어났는지 기준으로 나눈다.

```
order-created       → 주문 생성됨
order-cancelled     → 주문 취소됨
payment-completed   → 결제 완료됨
payment-failed      → 결제 실패됨
user-signed-up      → 회원가입
user-logged-in      → 로그인
product-stock-updated → 재고 변경됨
```

**기준 2: 소비자(Consumer) 기준**

어떤 서비스가 읽을 것인지를 기준으로 나누는 방법.
하지만 이 방식은 Producer가 Consumer를 알아야 하므로 결합도가 높아진다. 일반적으로 권장하지 않음.

```
// 비권장 패턴
notification-service-events  → 알림 서비스용
analytics-service-events      → 분석 서비스용
```

**기준 3: 처리 특성별**

메시지 크기, 처리 속도, 중요도 등이 다를 때 분리.

```
orders-realtime     → 빠른 처리 필요, 보존 기간 짧게 (1일)
orders-archive      → 분석용, 보존 기간 길게 (30일)
user-activity-logs  → 대용량, 느린 처리 허용
payment-events      → 중요, replication factor 높게 (3)
```

**기준 4: 팀/서비스 오너십별**

대규모 조직에서는 팀 단위로 Topic 네임스페이스를 구분하기도 한다.

```
order-team.order-created
order-team.order-cancelled
payment-team.payment-completed
payment-team.refund-processed
```

### Topic 이름 컨벤션 예시

```
// 권장 패턴
{도메인}-{이벤트}            → order-created, user-signed-up
{팀}.{도메인}.{이벤트}       → commerce.order.created
{도메인}.{이벤트}.{환경}     → order.created.prod

// 피해야 할 패턴
events                        → 너무 포괄적
data                          → 의미 없음
orderServiceToPaymentService  → Consumer를 이름에 넣으면 변경 시 이름이 이상해짐
```

### Topic을 너무 많이 만들면?

Topic 자체는 가볍지만 Partition이 많아지면 Broker에 부하가 생긴다.
- 너무 잘게 쪼개면: 관리 복잡, Rebalancing 자주 발생
- 너무 뭉뚱그리면: Consumer가 불필요한 메시지까지 처리, 필터링 비용 발생

적정 수준: **하나의 Topic이 하나의 "일어난 사건"을 나타내도록** 설계하는 것이 기본.

---

## 동작 원리

### 1. 메시지 저장 방식 (append-only log)

```
Partition 0 (디스크 파일):
  [offset 0: msg] [offset 1: msg] [offset 2: msg] [offset 3: msg] ...
                                                                    ↑
                                                              항상 끝에 추가
```

- 중간 삽입/수정 없이 **끝에만 추가** → HDD도 빠른 순차 I/O 가능
- 메시지를 Consumer가 읽어도 **삭제하지 않음**
  - 설정한 보존 기간(`retention.ms`) 또는 크기(`retention.bytes`) 도달 시 삭제
  - 덕분에 여러 Consumer Group이 같은 메시지를 독립적으로 읽을 수 있음
  - 오래된 offset으로 되돌아가서 **재처리**도 가능

### 2. Replication (복제)

Broker 하나가 죽어도 데이터가 유실되지 않도록 다른 Broker에 복제한다.

```
replication.factor = 3 설정 시:

Partition 0
  Broker 1: Leader   ← Producer가 여기에 씀, Consumer가 여기서 읽음
  Broker 2: Follower ← Leader에서 복제받음
  Broker 3: Follower ← Leader에서 복제받음

Broker 1이 죽으면:
  Broker 2가 새 Leader로 자동 선출됨
  Broker 3은 새 Leader(Broker 2)에서 복제 계속
```

- `acks=all` 설정 시 모든 Follower에 복제 완료된 후 Producer에게 응답 → 데이터 손실 없음
- `acks=1` 설정 시 Leader에만 저장되면 응답 → 빠르지만 Leader 죽으면 손실 가능

### 3. ZooKeeper / KRaft

- 전통적으로 **ZooKeeper**가 Broker 상태, Leader 선출 등 메타데이터 관리
- Kafka 2.8+부터 **KRaft 모드** 도입 → Kafka 자체적으로 메타데이터 관리
- Kafka 4.0부터 KRaft가 기본값 (ZooKeeper 의존성 제거)

---

## 전달 보장 수준 (Delivery Semantics)

| 수준 | 설명 | 중복 가능성 | 손실 가능성 | 적합한 상황 |
|------|------|------------|------------|------------|
| At most once | 최대 1번 전달 | 없음 | 있음 | 로그 수집 (일부 손실 허용) |
| At least once | 최소 1번 전달 | 있음 | 없음 | 일반적인 경우 (멱등성 처리 필요) |
| Exactly once | 정확히 1번 전달 | 없음 | 없음 | 결제, 재고 (중복/손실 모두 불허) |

- **At least once**가 일반적인 기본값
- **Exactly once**는 `enable.idempotence=true` + 트랜잭션 API 사용

---

## 전통적인 메시지 큐(RabbitMQ 등)와의 차이

| | Kafka | 전통 MQ (RabbitMQ 등) |
|---|---|---|
| 메시지 삭제 | 보존 기간/크기까지 유지 | 소비 즉시 삭제 |
| 재처리 | offset 되돌려서 가능 | 어려움 (이미 삭제됨) |
| 여러 소비자 | Group별로 독립 소비 | 메시지 하나를 한 Consumer만 받음 |
| 순서 보장 | Partition 내 보장 | Queue 내 보장 |
| 처리량 | 매우 높음 (수백만/초) | 상대적으로 낮음 |
| 라우팅 | Topic 기반 단순 | Exchange, Binding 등 복잡한 라우팅 가능 |
| 주 용도 | 대용량 스트리밍, 이벤트 로그 | 작업 큐, 복잡한 라우팅 |

> RabbitMQ는 "작업 분배" (하나의 메시지를 하나의 Worker가 처리)에 적합하고,
> Kafka는 "이벤트 스트리밍" (하나의 이벤트를 여러 서비스가 각자 소비)에 적합하다.

---

## 주요 설정 키워드

| 설정 | 의미 |
|------|------|
| `retention.ms` | 메시지 보존 기간 (기본 7일 = 604800000) |
| `retention.bytes` | Partition당 최대 저장 크기 (-1이면 무제한) |
| `replication.factor` | 복제 수 (보통 3, Broker 수 이하여야 함) |
| `num.partitions` | Topic 생성 시 기본 Partition 수 |
| `acks` | Producer 응답 기준 (0=안기다림, 1=Leader만, all=전체) |
| `auto.offset.reset` | 처음 읽을 때 시작 위치 (earliest=처음부터, latest=이후부터) |
| `group.id` | Consumer Group 식별자 |
| `enable.idempotence` | Producer 중복 전송 방지 (Exactly once용) |