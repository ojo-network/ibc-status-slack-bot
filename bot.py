import slack
import os
from dotenv import load_dotenv
from util import get_latest_block_height, get_latest_client_height, get_pending_packets

class IBC_Channel:
    def __init__(
            self,
            chainAName,
            chainBName,
            chainAChannelId,
            chainBChannelId,
            chainAPort,
            chainBPort,
            chainAEndpoint,
            chainBEndpoint,
            chainAClient,
            chainBClient,
            chainAMaxClientLag,
            chainBMaxClientLag,
            slackClient,
            slackChannel
        ):
        self.chainA = {
            "name": chainAName,
            "channelId": chainAChannelId,
            "port": chainAPort,
            "client": chainAClient,
            "endpoint": chainAEndpoint,
            "maxClientLag": int(chainAMaxClientLag)
        }
        self.chainB = {
            "name": chainBName,
            "channelId": chainBChannelId,
            "port": chainBPort,
            "client": chainBClient,
            "endpoint": chainBEndpoint,
            "maxClientLag": int(chainBMaxClientLag)
        }
        self.slackClient = slackClient
        self.slackChannel = slackChannel

    # Query last update height of each chain's ibc client and check wether its
    # behind the chain's current height by more than the chain's maxClientLag.
    def checkClients(self):
        # Check if client on Chain A hasn't been updated
        chain_b_latest_block = get_latest_block_height(self.chainB["endpoint"])
        chain_a_latest_client_block = get_latest_client_height(self.chainA["endpoint"], self.chainA["client"])
        if chain_b_latest_block and chain_a_latest_client_block and chain_b_latest_block - chain_a_latest_client_block > self.chainA["maxClientLag"]:
            self.slackClient.chat_postMessage(
                channel='#' + self.slackChannel,
                text=f"""WARNING: {self.chainA['name']}'s IBC client is more than {self.chainA["maxClientLag"]} blocks behind.
                    {self.chainB['name']} Chain height: {chain_b_latest_block},
                    {self.chainA['name']} Client height: {chain_a_latest_client_block}"""
            )

        # Check if client on Chain B hasn't been updated
        chain_a_latest_block = get_latest_block_height(self.chainA["endpoint"])
        chain_b_latest_client_block = get_latest_client_height(self.chainB["endpoint"], self.chainB["client"])
        if chain_a_latest_block and chain_b_latest_client_block and chain_a_latest_block - chain_b_latest_client_block > self.chainB["maxClientLag"]:
            self.slackClient.chat_postMessage(
                channel='#' + self.slackChannel,
                text=f"""WARNING: {self.chainB['name']}'s IBC client is more than {self.chainB["maxClientLag"]} blocks behind.
                    {self.chainA['name']} Chain height: {chain_a_latest_block},
                    {self.chainB['name']} Client height: {chain_b_latest_client_block}"""
            )

    def checkPendingPackets(self):
        # Check for pending packets in Chain A
        pending_packets_a = get_pending_packets(self.chainA["endpoint"], self.chainA["channelId"], self.chainA["port"])

        # Check for pending packets in Chain B
        pending_packets_b = get_pending_packets(self.chainB["endpoint"], self.chainB["channelId"], self.chainB["port"])

def monitor_channels(channels):
    for channel in channels:
        channel.checkClients()
        channel.checkPendingPackets()

    print("Completed checks")

def load_channels(slackClient, slackChannel):
    channels = []
    env_vars = os.environ

    # Iterate through all environment variables to find channel-related ones
    channel_data = {}
    for key, value in env_vars.items():
        if key.startswith("CHANNEL_"):
            _, idx, attr = key.split("_", 2)
            if idx not in channel_data:
                channel_data[idx] = {}
            channel_data[idx][attr] = value

    # Create IBC_Channel instances
    for idx, data in channel_data.items():
        chainAChannelId = data.get("CHAINAID")
        chainBChannelId = data.get("CHAINBID")
        chainAPort = data.get("CHAINAPORT")
        chainBPort = data.get("CHAINBPORT")
        chainAEndpoint = data.get("CHAINAENDPOINT")
        chainBEndpoint = data.get("CHAINBENDPOINT")
        chainAClient = data.get("CHAINACLIENT")
        chainBClient = data.get("CHAINBCLIENT")
        chainAName = data.get("CHAINANAME")
        chainBName = data.get("CHAINBNAME")
        chainAMaxClientLag = data.get("CHAINAMAXCLIENTLAG")
        chainBMaxClientLag = data.get("CHAINBMAXCLIENTLAG")

        channel = IBC_Channel(
            chainAName, chainBName, chainAChannelId, chainBChannelId, chainAPort, chainBPort,
            chainAEndpoint, chainBEndpoint, chainAClient, chainBClient,
            chainAMaxClientLag, chainBMaxClientLag, slackClient, slackChannel
        )
        channels.append(channel)

    return channels

if __name__ == "__main__":
    load_dotenv()
    monitor_channels(
        load_channels(
            slack.WebClient(token=os.environ['SLACK_TOKEN']),
            os.environ['SLACK_CHANNEL']
        )
    )
