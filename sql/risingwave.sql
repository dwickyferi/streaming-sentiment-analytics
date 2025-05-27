-- Create table
CREATE TABLE live_chat_sentiment (
    message_id TEXT PRIMARY KEY,
    message TEXT ,
    author_channel_id TEXT  ,
    author TEXT ,
    timestamp_message timestamp  
);

-- Create a function to perform sentiment analysis
CREATE FUNCTION sentiment_analysis(VARCHAR) RETURNS VARCHAR
AS sentiment_analysis USING LINK 'http://192.168.200.180:8815';


-- Create a materialized view to perform sentiment analysis on live chat messages
create materialized view chat_sentiment as
select 
	message_id,
	message,
	author_channel_id,
	author,
	timestamp_message,
	sentiment_analysis(message)
from live_chat_sentiment;

-- Create Iceberg Sink
CREATE SINK sink_chat_sentiment FROM chat_sentiment
WITH (
    connector = 'iceberg',
    type = 'upsert',
    primary_key = 'message_id',
    s3.endpoint = 'http://minio:9000',
    s3.region = 'us-east-1',
    s3.access.key = 'admin',
    s3.secret.key = 'password',
    s3.path.style.access = 'true',
    catalog.type = 'rest',
    catalog.uri = 'http://amoro:1630/api/iceberg/rest',
    catalag.name = 'icelake',
    warehouse.path = 'icelake',
    database.name = 'warehouse',
    table.name = 'chat_sentiment',
    create_table_if_not_exists = TRUE
);