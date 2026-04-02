"""
03_partitions.py
파티션 직접 지정 — 특정 파티션만 구독하거나, 파티션별 오프셋 제어.

목표:
- assign()으로 특정 파티션만 읽기
- seek()으로 원하는 오프셋부터 다시 읽기
- 파티션이 어떻게 데이터를 분산 저장하는지 체감

사전 준비 (토픽을 파티션 3개로 생성):
  kafka-topics.sh --create --topic binance-trades \
    --partitions 3 --replication-factor 1 \
    --bootstrap-server localhost:9092
"""

import json
from kafka import KafkaConsumer, TopicPartition

KAFKA_TOPIC = "binance-trades"
KAFKA_BOOTSTRAP = "localhost:9092"
TARGET_PARTITION = 0   # 읽을 파티션 번호

consumer = KafkaConsumer(
    bootstrap_servers=KAFKA_BOOTSTRAP,
    value_deserializer=lambda v: json.loads(v.decode("utf-8")),
)

# 특정 파티션만 직접 할당 (group coordinator 없이)
tp = TopicPartition(KAFKA_TOPIC, TARGET_PARTITION)
consumer.assign([tp])

# 처음부터 읽고 싶으면 아래 주석 해제
# consumer.seek_to_beginning(tp)

print(f"[CONSUMER] Assigned to partition={TARGET_PARTITION}")

for message in consumer:
    trade = message.value
    print(
        f"[CONSUMER] partition={message.partition} offset={message.offset} "
        f"| {trade['symbol']} price={trade['price']}"
    )
