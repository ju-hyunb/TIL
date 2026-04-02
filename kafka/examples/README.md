# Kafka 실습

바이낸스 API로 실시간 가격 데이터를 Kafka에 흘려보내면서 단계별로 Kafka 개념을 익히는 실습.

## 환경 설정

```bash
pip install kafka-python websocket-client
```

Kafka는 로컬에 Docker로 띄운다고 가정:

```bash
docker run -d --name kafka \
  -p 9092:9092 \
  -e KAFKA_ADVERTISED_LISTENERS=PLAINTEXT://localhost:9092 \
  apache/kafka:latest
```

## 실습 순서

| 파일 | 내용 |
|------|------|
| `producer.py` | 바이낸스 WebSocket → Kafka 토픽 발행 |
| `01_basic_consumer.py` | 기본 Consumer — 메시지 읽기 |
| `02_consumer_groups.py` | Consumer Group — 여러 Consumer가 파티션 나눠 처리 |
| `03_partitions.py` | 파티션 직접 지정해서 발행/구독 |

## 실행 방법

터미널 두 개 열고:
```bash
# 터미널 1
python producer.py

# 터미널 2
python 01_basic_consumer.py
```
