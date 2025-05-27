import re
from datetime import datetime
from arrow_udf import udf, udtf, UdfServer
import os
import time
import logging
import argparse
from nltk.sentiment.vader import SentimentIntensityAnalyzer

import nltk
import ssl

try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context

# Download VADER lexicon if not already present
nltk.download('vader_lexicon')


@udf(input_types=["VARCHAR"], result_type="VARCHAR")
def sentiment_analysis(message: str) -> str:
    """
    Perform sentiment analysis on a given message using VADER sentiment analysis.
    Args:
        message (str): The input message to analyze.
    Returns:
        str: The sentiment of the message - 'positive', 'negative', or 'neutral'.
    """
    sid = SentimentIntensityAnalyzer()
    scores = sid.polarity_scores(message)
    compound = scores['compound']
    if compound > 0.05:
        return 'positive'
    elif compound < -0.05:
        return 'negative'
    else:
        return 'neutral'

if __name__ == '__main__':
    # Create a UDF server and register the functions
    server = UdfServer(location="0.0.0.0:8815") # You can use any available port in your system. Here we use port 8815.
    server.add_function(sentiment_analysis)
    # Start the UDF server
    server.serve()