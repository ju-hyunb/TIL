"""
01_basic_consumer.py
가장 기본적인 Consumer — Kafka 토픽에서 메시지를 읽어 출력.

목표:
- Consumer가 토픽을 구독하고 메시지를 polling하는 흐름 이해
- auto_offset_reset="earliest" vs "latest" 차이 확인
"""

import json
from kafka import KafkaConsumer

KAFKA_TOPIC = "binance-trades"
KAFKA_BOOTSTRAP = "localhost:9092"

consumer = KafkaConsumer(
    KAFKA_TOPIC,
    bootstrap_servers=KAFKA_BOOTSTRAP,
    value_deserializer=lambda v: json.loads(v.decode("utf-8")),
    auto_offset_reset="latest",   # "earliest"로 바꾸면 처음부터 읽음
    enable_auto_commit=True,
)

print(f"[CONSUMER] Listening to topic: {KAFKA_TOPIC}")

for message in consumer:
    trade = message.value
    print(
        f"[CONSUMER] partition={message.partition} offset={message.offset} "
        f"| {trade['symbol']} price={trade['price']}"
    )
