import twitter
import time
import os

RETAINING_TIME_IN_SECONDS = 5 * 24 * 3600
RETAINING_LIKES = 20
MINIMUM_TWEET_NUM = 100


def remove_tweet(api, status, time_now):
    if time_now - status.created_at_in_seconds > RETAINING_TIME_IN_SECONDS:
        api.DestroyStatus(status_id=status.id)
        return True

    return False


def unlike_tweet(api, status):
    deleted = False
    try_count = 0
    while not deleted and try_count < 3:
        try:
            api.DestroyFavorite(status_id=status.id)
            try_count += 1
            deleted = True
        except twitter.TwitterError as e:
            print(e, status)
            time.sleep(0.1)

    return deleted


def main():
    time_now = time.time()
    api = twitter.Api(consumer_key=os.environ.get("TWITTER_CONSUMER_KEY"),
                      consumer_secret=os.environ.get("TWITTER_CONSUMER_SECRET"),
                      access_token_key=os.environ.get("TWITTER_ACCESS_TOKEN_KEY"),
                      access_token_secret=os.environ.get("TWITTER_ACCESS_TOKEN_SECRET"))
    credentials = api.VerifyCredentials()

    # REMOVE TWEETS
    removing_max_count = max(0, credentials.statuses_count - MINIMUM_TWEET_NUM)
    max_id = None
    removed_count = 0
    while True:
        timeline = api.GetUserTimeline(user_id=credentials.id,
                                       count=200,
                                       max_id=max_id,
                                       include_rts=True,
                                       trim_user=False,
                                       exclude_replies=False)

        if len(timeline) == 0 or removing_max_count <= removed_count:
            break

        for status in timeline:
            max_id = status.id - 1
            if remove_tweet(api, status, time_now):
                removed_count += 1
                if removing_max_count <= removed_count:
                    break

    print("{} tweets removed.".format(removed_count))

    # REMOVE LIKES
    max_id = None
    unliked_count = 0
    iter_count = 0
    while True:
        favorites = api.GetFavorites(user_id=credentials.id,
                                     count=200,
                                     max_id=max_id)
        if len(favorites) == 0:
            break

        for status in favorites:
            max_id = status.id - 1
            if iter_count >= RETAINING_LIKES:
                if unlike_tweet(api, status):
                    unliked_count += 1
            iter_count += 1

    print("{} tweets unliked.".format(unliked_count))


if __name__ == "__main__":
    main()
