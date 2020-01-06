import slack

import foodbot_util


class SlackClient:
    client: slack.WebClient = None

    def __init__(self):
        configuration = foodbot_util.configuration

        self.token_conf = configuration["token"]
        self.client_conf = configuration["client"]


class BotClient(SlackClient):
    def __init__(self):
        SlackClient.__init__(self)
        bot_token = self.token_conf["bot"]
        self.client = slack.WebClient(bot_token)


class OAuthClient(SlackClient):
    def __init__(self):
        SlackClient.__init__(self)
        oauth_token = self.token_conf["oauth"]
        client_id = self.client_conf["id"]
        client_secret = self.client_conf["secret"]
        self.client = slack.WebClient(token=oauth_token
                                      # ,
                                      # client_id=client_id,
                                      # client_secret=client_secret
                                      )
