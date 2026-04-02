# Apache Kafka 기본 개념 및 동작 원리

## Kafka란?

Apache Kafka는 **분산 이벤트 스트리밍 플랫폼**이다.

단순한 메시지 큐라기보다, 대규모 실시간 데이터 흐름을 안정적으로 저장하고 전달하는 **이벤트 로그 기반 데이터 허브**에 가깝다.

---

## 왜 Kafka를 사용하는가?

### 문제 상황: 서비스가 많아질수록 연결이 복잡해진다

서비스가 여러 개 있고, 서로 데이터를 주고받아야 한다.

```text
[주문 서비스] → [결제 서비스]
[주문 서비스] → [재고 서비스]
[주문 서비스] → [알림 서비스]
[주문 서비스] → [분석 서비스]
```

직접 연결(HTTP 호출 등)하면:

- 상대 서비스가 죽어 있으면 요청도 실패 → 강한 결합(Coupling)
- 서비스가 늘어날수록 연결 수가 폭발적으로 증가
- 데이터를 여러 곳에 보내려면 코드가 복잡해짐

### Kafka로 해결

```text
[주문 서비스] → Kafka(order-events topic)
                        ↓
          ┌─────────────┼─────────────┐
     [결제 서비스]  [재고 서비스]  [알림 서비스]  [분석 서비스]
```

- 주문 서비스는 Kafka에 메시지만 보내면 된다 → **느슨한 결합(Decoupling)**
- 각 서비스는 Kafka에서 독립적으로 읽는다 → 한 서비스가 느려도 나머지 영향이 적다
- 새 서비스가 추가돼도 Producer 코드를 거의 건드리지 않아도 된다

### Kafka의 핵심 장점 요약

| 장점 | 설명 |
|------|------|
| **높은 처리량** | 대용량 이벤트를 빠르게 처리할 수 있음 |
| **낮은 지연** | append-only 로그 기반이라 저장/읽기 효율이 좋음 |
| **내결함성** | 복제를 통해 장애 상황에서도 복구 가능 |
| **확장성** | Broker/Partition 추가로 수평 확장 가능 |
| **메시지 보존** | 읽어도 바로 삭제되지 않음 |
| **순서 보장** | Partition 내부에서 순서 보장 |
| **느슨한 결합** | Producer와 Consumer가 직접 서로를 몰라도 됨 |

---

## 핵심 구성 요소

### 전체 구조

```text
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
- 메시지에 **Key**를 붙일 수 있음
- 같은 Key는 같은 Partition으로 가기 쉬워서 **Key 단위 순서 보장**에 유리함

예:
- 같은 `user_id`를 Key로 보내면 같은 유저 이벤트가 같은 Partition으로 모일 가능성이 높다
- 같은 `order_id`를 Key로 보내면 주문 단위 흐름 추적이 쉬워진다

```text
producer.send("order-events", userId, orderMessage)
→ hash(userId) % partitionCount
```

#### Key가 없으면 어떻게 될까?

- Partition을 직접 지정하지 않고
- Key도 없으면

기본 파티셔너가 **sticky partition 방식**으로 분배한다.

즉, 예전처럼 단순 라운드로빈이라고만 보기보다,  
**일정 배치가 찰 때까지 한 Partition에 붙였다가 다음 Partition으로 옮기는 방식**에 가깝다.

이 방식은 작은 메시지를 보낼 때도 batching 효율을 높여준다.

---

### Consumer (소비자)

- 메시지를 Kafka에서 **읽는** 쪽
- **Consumer Group** 단위로 묶여서 동작
- 읽은 위치(Offset)를 커밋하여 어디까지 읽었는지 추적

---

### Broker

- Kafka 서버 인스턴스 하나
- 메시지를 **디스크에 저장**하고 Producer/Consumer 요청을 처리
- 여러 Broker가 모이면 **Cluster**를 구성
- 각 Broker는 일부 Partition의 **Leader** 또는 **Follower** 역할을 맡음

```text
Cluster (Broker 3대)
├── Broker 1: order-events Partition 0 Leader, payment-events Partition 1 Follower
├── Broker 2: order-events Partition 1 Leader, order-events Partition 0 Follower
└── Broker 3: order-events Partition 2 Leader, order-events Partition 1 Follower
```

---

### Topic

- 메시지를 분류하는 **논리적 단위**
- 쉽게 말하면 비슷한 성격의 이벤트를 묶는 **이벤트 카테고리**
- 하나의 Topic은 여러 **Partition**으로 나뉠 수 있음

예:
- `order-events`
- `payment-events`
- `shipment-events`

---

### Partition

- Topic의 **물리적 분할 단위**
- 각 Partition은 **순서가 보장된 append-only 로그**
- Partition 수가 많을수록 병렬 처리 여지가 커진다

```text
Topic: order-events (Partition 3개)

Partition 0: [order#1] [order#4] [order#7] ...
Partition 1: [order#2] [order#5] [order#8] ...
Partition 2: [order#3] [order#6] [order#9] ...
```

> 주의: **Topic 전체 순서**는 보장되지 않는다.  
> **Partition 내부 순서만** 보장된다.

---

### Offset

- Partition 내 각 메시지에 붙는 **순서 번호**
- Consumer가 어디까지 읽었는지 추적하는 **책갈피**
- Offset을 커밋하면 재시작 후 이어서 읽을 수 있다

```text
Partition 0
offset 0: order#1
offset 1: order#4
offset 2: order#7  ← 여기까지 읽고 커밋
offset 3: order#9  ← 다음에 여기서 이어서 시작
```

---

## Consumer Group

Consumer Group은 Kafka에서 가장 중요한 개념 중 하나다.

### 기본 개념

**Consumer Group = 하나의 애플리케이션을 여러 인스턴스로 실행하는 단위**

같은 Group에 속한 Consumer들은 Topic의 Partition을 나눠 읽는다.  
즉, 같은 메시지를 중복 처리하지 않고 **병렬 처리**한다.

### 예시

```text
Topic: order-events (Partition 3개)

[초기]
Consumer Group "order-processor"
- Consumer 1 → Partition 0, 1, 2 모두 처리

[스케일아웃]
- Consumer 1 → Partition 0
- Consumer 2 → Partition 1
- Consumer 3 → Partition 2
```

### Consumer 수와 Partition 수의 관계

```text
Case 1: Consumer 수 = Partition 수
  Partition 0 → Consumer 1
  Partition 1 → Consumer 2
  Partition 2 → Consumer 3

Case 2: Consumer 수 < Partition 수
  Consumer 1이 여러 Partition 담당

Case 3: Consumer 수 > Partition 수
  남는 Consumer는 대기
```

> 병렬 처리의 최대 단위는 **Partition 수**다.

### 여러 Consumer Group이 같은 Topic을 읽는 경우

각 Consumer Group은 **완전히 독립적**이다.

```text
Topic: order-events

Consumer Group "order-processor"
→ 주문 처리

Consumer Group "analytics-service"
→ 분석 집계

Consumer Group "notification-service"
→ 알림 전송
```

같은 Topic을 읽더라도  
각 Group은 각자 Offset을 따로 관리한다.

즉:
- 한 서비스가 느려도 다른 서비스에 직접 영향이 적고
- 새 서비스가 생겨도 새 Consumer Group만 추가하면 된다

### Rebalancing

Consumer가 추가되거나 죽으면 Partition 할당이 다시 조정된다.

```text
[정상]
Consumer 1 → Partition 0
Consumer 2 → Partition 1
Consumer 3 → Partition 2

[Consumer 2 장애]
→ Rebalancing
Consumer 1 → Partition 0, 1
Consumer 3 → Partition 2
```

리밸런싱 중에는 잠깐 소비가 멈출 수 있다.  
그래서 너무 자주 발생하면 성능에 영향을 줄 수 있다.

---

## Topic 분류의 장점과 기준

### 왜 Topic 분류가 필요한가?

모든 메시지를 한 Topic에 몰아넣으면:

- 메시지 의미가 불명확해짐
- 관련 없는 Consumer도 전체 메시지를 다 읽어야 함
- 보존 기간, 복제 수, 권한 정책을 세밀하게 나누기 어려움

Topic으로 분리하면:

- Consumer가 필요한 이벤트만 구독 가능
- Topic별 설정 분리 가능
- 시스템에서 어떤 데이터가 흐르는지 명확해짐

### Topic 분류 기준

#### 1. 도메인 / 이벤트 유형 기준

가장 일반적이다.

```text
order.created
order.cancelled
payment.completed
payment.failed
user.signed-up
product.stock.updated
```

#### 2. 처리 특성 기준

처리 속도, 중요도, 보존 정책이 다르면 분리할 수 있다.

```text
orders.realtime
orders.archive
payment.events
user.activity.logs
```

#### 3. 팀 / 서비스 오너십 기준

조직이 커지면 팀 단위 네임스페이스를 쓰기도 한다.

```text
commerce.order.created
payment.refund.processed
inventory.stock.updated
```

### Topic 이름 예시

```text
order.created
payment.completed
commerce.order.created
order.created.prod
```

### 피해야 할 이름

```text
events
data
orderServiceToPaymentService
```

- 너무 포괄적이거나
- 소비자 이름이 토픽 이름에 직접 들어가면
나중에 구조가 바뀔 때 어색해진다.

### Topic을 너무 많이 만들면?

Topic 자체보다 **Partition 수 증가**가 운영 복잡도에 더 큰 영향을 준다.

- 너무 잘게 쪼개면 관리 포인트가 늘어남
- 너무 뭉치면 Consumer가 불필요한 메시지까지 처리하게 됨

실무적으로는 보통  
**같은 의미, 비슷한 스키마, 비슷한 소비 패턴, 비슷한 보존 정책을 가진 이벤트를 하나의 Topic으로 묶는 방식**이 자연스럽다.

---

## 동작 원리

### 1. 메시지 저장 방식 (append-only log)

```text
Partition 0 (디스크 파일)
[offset 0: msg] [offset 1: msg] [offset 2: msg] [offset 3: msg] ...
                                                             ↑
                                                       항상 끝에 추가
```

- 중간 삽입/수정 없이 끝에만 추가
- Consumer가 읽어도 바로 삭제되지 않음
- 설정된 보존 기간 또는 크기 제한에 따라 나중에 정리됨
- 여러 Consumer Group이 같은 메시지를 독립적으로 읽을 수 있음
- Offset을 되돌려 재처리도 가능

### 2. Replication (복제)

Broker 하나가 죽어도 복구 가능하도록 다른 Broker에 복제한다.

```text
replication.factor = 3

Partition 0
- Broker 1: Leader
- Broker 2: Follower
- Broker 3: Follower
```

Leader가 죽으면 다른 복제본이 새 Leader가 될 수 있다.

#### `acks=all`은 무조건 손실이 없다는 뜻일까?

아니다. `acks=all`은 가장 강한 쓰기 보장이지만,  
실제 내구성은 **ISR(in-sync replicas)** 상태와 **`min.insync.replicas`** 설정을 함께 봐야 한다.

즉, 실무에서는 보통 아래를 같이 본다.

- `replication.factor`
- `acks=all`
- `min.insync.replicas`

예를 들어 복제본 3개 중 최소 2개 이상이 동기화돼 있어야 성공하게 만들 수 있다.

### 3. ZooKeeper / KRaft

Kafka는 과거에 ZooKeeper를 사용해 메타데이터를 관리했다.

하지만 현재는 **KRaft** 기반으로 전환되었고,  
**Kafka 4.0부터는 ZooKeeper 모드가 제거되어 KRaft만 지원**한다.

즉, 최신 Kafka를 공부할 때는 KRaft 기준으로 이해하는 것이 맞다.

---

## 전달 보장 수준 (Delivery Semantics)

| 수준 | 설명 | 중복 가능성 | 손실 가능성 | 적합한 상황 |
|------|------|------------|------------|------------|
| At most once | 최대 1번 전달 | 없음 | 있음 | 일부 로그성 데이터 |
| At least once | 최소 1번 전달 | 있음 | 낮음 | 일반적인 이벤트 처리 |
| Exactly once | 정확히 1번 처리 지향 | 매우 낮음 | 매우 낮음 | 중복/손실 모두 민감한 경우 |

### 정리

- **At least once**가 일반적으로 가장 많이 쓰인다
- **Idempotence**는 Producer 재시도 시 중복 쓰기를 줄이거나 방지하는 데 중요하다
- **Transaction**은 여러 Partition/Topic에 대한 원자적 처리를 다룰 때 사용된다

즉:

- `enable.idempotence=true`
  → Producer 중복 전송 방지에 도움
- Transaction API
  → 더 넓은 범위의 exactly-once 처리에 사용

---

## 전통적인 메시지 큐(RabbitMQ 등)와의 차이

| 항목 | Kafka | RabbitMQ 등 전통 MQ |
|---|---|---|
| 기본 모델 | 이벤트 로그 | 큐 기반 메시징 |
| 메시지 보존 | 일정 기간 보존 | ack 이후 제거되는 패턴이 일반적 |
| 재처리 | Offset 기반 재처리 용이 | 일반적으로 Kafka보다 덜 자연스러움 |
| 여러 소비자 | Consumer Group별 독립 소비 | Exchange/Binding으로 fanout 가능 |
| 순서 보장 | Partition 내 보장 | Queue 단위 처리 모델 |
| 강점 | 대용량 스트리밍, 이벤트 백본 | 작업 큐, 라우팅, request/reply |

> 단순히  
> `Kafka = 무조건 우월`,  
> `RabbitMQ = 구식`  
> 으로 보면 안 된다.
>
> 둘은 잘하는 일이 다르다.
>
> - Kafka: 이벤트 스트리밍, 로그 보존, 재처리
> - RabbitMQ: 작업 큐, 복잡한 라우팅, 메시지 브로커 패턴

---

## 주요 설정 키워드

| 설정 | 의미 |
|------|------|
| `retention.ms` | Topic 단위 메시지 보존 기간 |
| `retention.bytes` | Topic/Partition 저장 크기 제한 |
| `replication.factor` | 복제 수 |
| `num.partitions` | Topic의 Partition 수 |
| `acks` | Producer 응답 기준 |
| `auto.offset.reset` | 처음 읽을 때 시작 위치 |
| `group.id` | Consumer Group 식별자 |
| `enable.idempotence` | Producer 중복 전송 방지 |
| `min.insync.replicas` | `acks=all`일 때 쓰기 성공에 필요한 최소 ISR 수 |

> 참고로 Kafka의 기본 보존 기간은 보통 7일로 설명되며,  
> broker 기본 설정에서는 `log.retention.hours=168` 형태로 많이 본다.

---

## 한 줄 정리

Kafka는  
**이벤트를 Topic에 기록하고, 여러 Consumer Group이 이를 독립적으로 읽을 수 있게 해주는 분산 이벤트 스트리밍 플랫폼**이다.

핵심은 다음 네 가지다.

1. **Topic**: 이벤트를 분류하는 단위  
2. **Partition**: 병렬 처리와 순서 보장의 단위  
3. **Offset**: 어디까지 읽었는지 추적하는 위치  
4. **Consumer Group**: 같은 서비스를 여러 인스턴스로 병렬 처리하는 단위
