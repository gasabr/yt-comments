import sys
import json
import argparse

from apiclient.discovery import build
from apiclient.errors import HttpError
from YamJam import yamjam       # for managing secret keys
from datetime import datetime


parser = argparse.ArgumentParser(description='Download comments from youtube')
parser.add_argument(
        '--videoId', type=str, help='url of the video after v=')
args = parser.parse_args()

# Set DEVELOPER_KEY to the API key value from the APIs & auth > Registered apps
# tab of
#   https://cloud.google.com/console
# Please ensure that you have enabled the YouTube Data API for your project.
DEVELOPER_KEY = yamjam()['yt_comments']['YOUTUBE_KEY']
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"

YOUTUBE_URL_PREFIX = 'https://www.youtube.com/watch?v='

youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION,
        developerKey=DEVELOPER_KEY)

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
    # TODO: this should be unique user id, but as docs states,
    # everything exept name is optional, so for now let it be name
    # https://developers.google.com/youtube/v3/docs/comments#resource
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

    return response['items']


def yield_comments(threads):
    for thread in threads['items']:
        comment = parse_item(thread['snippet']['topLevelComment'])
        comment['source'] = YOUTUBE_URL_PREFIX + thread['snippet']['videoId']

        if thread['snippet']['totalReplyCount'] != 0:
            # additional call to API needed to receive all the comments,
            # see replies.comments[] part of docs here:
            # https://developers.google.com/youtube/v3/docs/commentThreads#resource
            for reply in get_replies(comment['comment_id']):
                reply['reply_to'] = comment['user_name']
                reply['source'] = YOUTUBE_URL_PREFIX \
                        + thread['snippet']['videoId']

                yield reply

        yield comment


def write_comments_to_file(comments, filename):
    '''
    Arguments:
        comments(dict): comments to be written to file
        filename(str) : name of the file to write comments into
    '''

    with open(filename, 'w') as fp:
        json.dump(comments, fp, indent=2, ensure_ascii=False)


def download_comments(video_id):
    threads = get_comment_threads({
        'videoId': video_id,
        'maxResults': _MAX_RESULTS_PER_QUERY,})

    # FIXME: this is dumb: using iterator to convert the thing into the list
    comments = list(yield_comments(threads))

    while 'nextPageToken' in threads:
        threads = get_comment_threads({
            'videoId': video_id,
            'maxResults': _MAX_RESULTS_PER_QUERY,
            'pageToken': threads['nextPageToken']})

        for comment in yield_comments(threads):
            comments.append(comment)

    return comments


def async_download_comments(video_id):
    # create a pool (queue) of threads to be downloaded for given video
    # create list of threads that will be polling (non-blocking) for the
    # videoId, when they got one -- they are going to download threads into
    # the list (create comments from it) and append it to the resulting vector
    pass


if __name__ == "__main__":
    try:
        video_id = args.videoId
    except AttributeError as e:
        sys.stderr.write('Please specify id of the video.\n')
        sys.exit(1)

    comments = download_comments(video_id)

    json.dump(comments, sys.stdout)
    print()

