"""
02_consumer_groups.py
Consumer Group — 같은 group_id를 가진 Consumer들이 파티션을 나눠 처리.

목표:
- 터미널 여러 개에서 이 파일을 동시에 실행해보기
- 각 Consumer가 서로 다른 파티션을 담당하는 것 확인
- group_id가 다르면 같은 메시지를 독립적으로 받는다는 것 확인

실험:
  터미널 A: python 02_consumer_groups.py
  터미널 B: python 02_consumer_groups.py  ← 같은 group_id → 파티션 분배
  터미널 C: GROUP_ID를 바꿔서 실행       ← 다른 group → 메시지 중복 수신
"""

import json
from kafka import KafkaConsumer

KAFKA_TOPIC = "binance-trades"
KAFKA_BOOTSTRAP = "localhost:9092"
GROUP_ID = "trade-group-1"   # 여기를 바꿔서 실험

consumer = KafkaConsumer(
    KAFKA_TOPIC,
    bootstrap_servers=KAFKA_BOOTSTRAP,
    group_id=GROUP_ID,
    value_deserializer=lambda v: json.loads(v.decode("utf-8")),
    auto_offset_reset="latest",
    enable_auto_commit=True,
)

print(f"[CONSUMER] group={GROUP_ID} | Listening to topic: {KAFKA_TOPIC}")

for message in consumer:
    trade = message.value
    print(
        f"[CONSUMER] group={GROUP_ID} partition={message.partition} offset={message.offset} "
        f"| {trade['symbol']} price={trade['price']}"
    )
