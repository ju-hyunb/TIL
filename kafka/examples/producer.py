"""
producer.py
바이낸스 WebSocket에서 실시간 BTC/USDT 체결 데이터를 받아 Kafka로 발행.
이 파일은 고정 — 모든 실습에서 공통으로 사용.
"""

import json
import websocket
from kafka import KafkaProducer

BINANCE_WS_URL = "wss://stream.binance.com:9443/ws/btcusdt@trade"
KAFKA_TOPIC = "binance-trades"
KAFKA_BOOTSTRAP = "localhost:9092"

producer = KafkaProducer(
    bootstrap_servers=KAFKA_BOOTSTRAP,
    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
)


def on_message(ws, message):
    data = json.loads(message)
    trade = {
        "symbol": data["s"],
        "price": data["p"],
        "quantity": data["q"],
        "time": data["T"],
    }
    producer.send(KAFKA_TOPIC, trade)
    print(f"[PRODUCER] {trade['symbol']} price={trade['price']}")


def on_error(ws, error):
    print(f"[ERROR] {error}")


def on_close(ws, *args):
    print("[PRODUCER] Connection closed")


def on_open(ws):
    print("[PRODUCER] Connected to Binance WebSocket")


if __name__ == "__main__":
    ws = websocket.WebSocketApp(
        BINANCE_WS_URL,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close,
        on_open=on_open,
    )
    ws.run_forever()
