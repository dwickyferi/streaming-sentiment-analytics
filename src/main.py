import requests
import time
import psycopg2

# YouTube API and RisingWave Database Configuration
# Replace with your actual YouTube API key and channel ID
API_KEY = "" 
CHANNEL_ID = ""

# RisingWave Database connection parameters
# Replace with your actual RisingWave database connection parameters
DB_PARAMS = {
    "dbname": "dev",
    "user": "root",
    "password": "",
    "host": "localhost",
    "port": "4566"
}

# Fetch Live Stream ID
def get_live_video_id() -> str:
    """
    Fetches the live video ID from the YouTube channel.
    Returns:
        str: The video ID of the live stream if available, otherwise None.
    """
    url = f"https://www.googleapis.com/youtube/v3/search?part=id&channelId={CHANNEL_ID}&eventType=live&type=video&key={API_KEY}"
    response = requests.get(url).json()
    if "items" in response and response["items"]:
        return response["items"][0]["id"]["videoId"]
    return None

# Fetch Live Chat ID
def get_live_chat_id(video_id) -> str:
    """
    Fetches the live chat ID for a given video ID.
    Args:
        video_id (str): The ID of the live video.
    Returns:
        str: The live chat ID if available, otherwise None.
    """
    url = f"https://www.googleapis.com/youtube/v3/videos?part=liveStreamingDetails&id={video_id}&key={API_KEY}"
    response = requests.get(url).json()
    return response["items"][0]["liveStreamingDetails"].get("activeLiveChatId")

# Stream chat messages from YouTube Live and insert into RisingWave
def stream_chat():
    """
    Streams chat messages from a YouTube Live stream and inserts them into a RisingWave database.
    This function connects to the YouTube API to fetch live chat messages and inserts them into a RisingWave database.
    It requires a valid YouTube API key and RisingWave database connection parameters.
    """
    conn = psycopg2.connect(**DB_PARAMS)
    cur = conn.cursor()
    video_id = get_live_video_id()
    if not video_id:
        print("No active live stream found.")
        return

    live_chat_id = get_live_chat_id(video_id)
    print(f"Streaming chat messages from YouTube Live Stream: {video_id}")

    next_page_token = None

    while True:
        url = f"https://www.googleapis.com/youtube/v3/liveChat/messages?liveChatId={live_chat_id}&part=snippet,authorDetails&key={API_KEY}"
        if next_page_token:
            url += f"&pageToken={next_page_token}"

        response = requests.get(url).json()
        messages = response.get("items", [])
        next_page_token = response.get("nextPageToken")

        for msg in messages:
            print(msg)
            
            try:
                message_data = {
                    "messageId": msg["id"],
                    "message": msg["snippet"]["displayMessage"] if "displayMessage" in msg["snippet"] else "unknown",
                    "authorChannelId": msg["authorDetails"]["channelId"],
                    "author": msg["authorDetails"]["displayName"],
                    "timestamp": msg["snippet"]["publishedAt"]
                }

                insert_query = """
                INSERT INTO live_chat_sentiment 
                (message_id, message, author_channel_id, author, timestamp_message)
                VALUES (%s, %s, %s, %s, %s)
                """
                cur.execute(insert_query, (
                    message_data["messageId"],
                    message_data["message"],
                    message_data["authorChannelId"],
                    message_data["author"],
                    message_data["timestamp"]
                ))
                conn.commit()
                print(f"Inserted: {message_data}")
            except Exception as e:
                print(f"Error inserting data: {e}")
                conn.rollback()
            finally:
                # Ensure the connection is closed properly
                cur.close()
                conn.close()
                
        polling_interval = int(response.get("pollingIntervalMillis", 5000)) / 1000.0
        time.sleep(polling_interval)

if __name__ == "__main__":
    stream_chat()