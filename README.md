# Streaming Sentiment Analytics

A real-time sentiment analysis pipeline that processes YouTube live chat messages using RisingWave and stores the results in Apache Iceberg, enabling downstream analytics. The system performs sentiment analysis on live chat messages using VADER sentiment analysis through a custom UDF.

## Architecture Overview

```
YouTube Live Chat → Python Stream → RisingWave → Apache Iceberg
                                     ↓
                               VADER Sentiment
                                 Analysis UDF
```

## Prerequisites

- Docker and Docker Compose
- Python 3.8+
- YouTube API Key
- Git

## Quick Start

1. **Clone the repository**

```bash
git clone <repository-url>
cd streaming-sentiment-analytics
```

2. **Install Python dependencies**

```bash
pip install -r requirements.txt
```

3. **Start the infrastructure**

```bash
docker-compose up -d
```

Wait until all services are healthy (approximately 2-3 minutes)

4. **Start the UDF Service**

```bash
python src/udf.py
```

This will start the sentiment analysis UDF service on port 8815

5. **Initialize RisingWave Schema**

```bash
psql -h localhost -p 4566 -d dev -U root -f sql/risingwave.sql
```

6. **Configure YouTube API**
   Update `src/main.py` with your YouTube API credentials:

```python
API_KEY = "your_youtube_api_key"
CHANNEL_ID = "target_youtube_channel_id"
```

7. **Start the Stream Process**

```bash
python src/main.py
```

## Component Details

### 1. Docker Infrastructure

- **RisingWave**: Stream processing engine (ports: 4566, 5690, 5691)
- **MinIO**: S3-compatible storage (ports: 9000, 9001)
- **Postgres**: Metadata storage
- **Amoro**: Apache Iceberg REST Catalog (port: 1630)
- **Trino**: SQL Query Engine (port: 8080)

### 2. Data Pipeline Components

#### YouTube Live Chat Streamer

- Located in `src/main.py`
- Connects to YouTube Live API
- Streams chat messages in real-time
- Inserts raw messages into RisingWave

#### Sentiment Analysis UDF

- Located in `src/udf.py`
- Uses VADER sentiment analysis
- Provides real-time sentiment scoring
- Returns: 'positive', 'negative', or 'neutral'

#### RisingWave Processing

- Creates materialized views for sentiment analysis
- Streams processed data to Apache Iceberg
- Schema defined in `sql/risingwave.sql`

## Data Flow

1. YouTube live chat messages are captured via the YouTube API
2. Messages are inserted into RisingWave's `live_chat_sentiment` table
3. The sentiment analysis UDF processes each message
4. Results are materialized in the `chat_sentiment` view
5. Processed data is continuously synced to Apache Iceberg

## Schema Definitions

### Live Chat Messages

```sql
CREATE TABLE live_chat_sentiment (
    message_id TEXT PRIMARY KEY,
    message TEXT,
    author_channel_id TEXT,
    author TEXT,
    timestamp_message timestamp
);
```

### Sentiment Analysis View

```sql
CREATE MATERIALIZED VIEW chat_sentiment AS
SELECT
    message_id,
    message,
    author_channel_id,
    author,
    timestamp_message,
    sentiment_analysis(message)
FROM live_chat_sentiment;
```

## Monitoring

- RisingWave Dashboard: http://localhost:5691
- MinIO Console: http://localhost:9001
- Trino UI: http://localhost:8080

## Troubleshooting

1. **RisingWave Connection Issues**

```bash
# Check RisingWave status
docker-compose ps
# View RisingWave logs
docker-compose logs -f meta-node-0
```

2. **UDF Service Issues**

```bash
# Check UDF service logs
docker logs -f $(docker ps -q --filter name=udf)
```

3. **Data Flow Verification**

```sql
-- Check incoming messages
SELECT COUNT(*) FROM live_chat_sentiment;

-- Verify sentiment analysis
SELECT sentiment_analysis, COUNT(*)
FROM chat_sentiment
GROUP BY sentiment_analysis;
```

## Performance Considerations

- Monitor RisingWave memory usage
- Adjust batch sizes for high-volume streams
- Consider scaling compute nodes for heavy loads

## License

This project is licensed under the MIT License - see the LICENSE file for details.
