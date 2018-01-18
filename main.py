from apiclient.discovery import build
from apiclient.errors import HttpError
from oauth2client.tools import argparser
from YamJam import yamjam       # for managing secret keys
from datetime import datetime
import json


# Set DEVELOPER_KEY to the API key value from the APIs & auth > Registered apps
# tab of
#   https://cloud.google.com/console
# Please ensure that you have enabled the YouTube Data API for your project.
DEVELOPER_KEY = yamjam()['code4navalny']['YOUTUBE_KEY']
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"

YOUTUBE_URL_PREFIX = 'https://www.youtube.com/watch?v='

youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION,
                developerKey=yamjam()['code4navalny']['YOUTUBE_KEY'])

_MAX_RESULTS_PER_QUERY = 100


def get_comment_threads(kwagrs):
    ''' Returns list of comment threads
    
    For list of kwargs visit 
    https://developers.google.com/youtube/v3/docs/commentThreads/list
    
    '''

    comments = youtube.commentThreads().list(
            part='id,snippet',
            **kwagrs,
            ).execute()

    return comments


def parse_item(snippet):
    comment = {}
    comment['comment_id'] = snippet['id']
    comment['user_name'] = snippet['snippet']['authorDisplayName']
    comment['timestamp'] = int(datetime.strptime(
            snippet['snippet']['publishedAt'],
            '%Y-%m-%dT%H:%M:%S.000Z').timestamp() * 1000)

    comment['comment'] = snippet['snippet']['textOriginal']
    comment['likes'] = snippet['snippet']['likeCount']

    return comment


def get_replies(parent_id):
    response = youtube.comments().list(
            part='id,snippet',
            parentId=parent_id).execute()
    comments = []

    for item in response['items']:
        comments.append(parse_item(item))

    return comments


def yield_comments(threads):
    for thread in threads['items']:
        comment = parse_item(thread['snippet']['topLevelComment'])
        comment['source'] = YOUTUBE_URL_PREFIX + thread['snippet']['videoId']

        if thread['snippet']['totalReplyCount'] != 0:
            for reply in get_replies(comment['comment_id']):
                reply['reply_to'] = comment['user_name']
                reply['source'] = YOUTUBE_URL_PREFIX \
                        + thread['snippet']['videoId']

                yield reply

        yield comment


if __name__ == "__main__":
    # TODO: get video id from cl argument
    videoId = '3ePzmHUSs7k'
    # TODO: get rid of maxResults
    threads = get_comment_threads({
        'videoId': videoId, 
        'maxResults': _MAX_RESULTS_PER_QUERY,})

    comments = list(yield_comments(threads))

    if 'nextPageToken' in threads:
        while threads['nextPageToken'] != '':
            threads = get_comment_threads({
                'videoId': videoId,  
                'maxResults': _MAX_RESULTS_PER_QUERY,
                'pageToken': threads['nextPageToken']})

            print(threads['nextPageToken'])

            for comment in yield_comments(threads):
                comments.append(comment)

    # TODO: move this to separate function
    with open(videoId + '.json', 'w') as fp:
        json.dump(comments, fp, indent=2, ensure_ascii=False)

