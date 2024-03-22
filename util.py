import requests

def get_latest_block_height(endpoint_url):
    try:
        response = requests.get(f"{endpoint_url}/cosmos/base/tendermint/v1beta1/blocks/latest")
        if response.status_code == 200:
            latest_block = response.json()
            return int(latest_block["block"]["header"]["height"])
        else:
            print(f"Error querying latest block height from {endpoint_url}: {response.status_code}")
    except Exception as e:
        print(f"Exception querying latest block height from {endpoint_url}: {e}")
    return None

def get_latest_client_height(endpoint_url, client_id):
    try:
        response = requests.get(f"{endpoint_url}/ibc/core/client/v1/client_states/{client_id}")
        if response.status_code == 200:
            client_state = response.json()
            return int(client_state["client_state"]["latest_height"]["revision_height"])
        else:
            print(f"Error querying latest client height from {endpoint_url}: {response.status_code}")
    except Exception as e:
        print(f"Exception querying latest client height from {endpoint_url}: {e}")
    return None

def get_pending_packets(endpoint_url, channel_id, port_id):
    try:
        commitments_url = f"{endpoint_url}/ibc/core/channel/v1/channels/{channel_id}/ports/{port_id}/packet_commitments"
        acks_url = f"{endpoint_url}/ibc/core/channel/v1/channels/{channel_id}/ports/{port_id}/packet_acknowledgements"

        commitments_response = requests.get(commitments_url)
        acks_response = requests.get(acks_url)

        if commitments_response.status_code == 200 and acks_response.status_code == 200:
            commitments = {d['sequence'] for d in commitments_response.json()['commitments']}
            acks = {d['sequence'] for d in acks_response.json()['acknowledgements']}

            # Packets that have been sent but not acknowledged
            pending_packets = commitments - acks
            return list(pending_packets)
    except Exception as e:
        print(f"Exception querying pending packets from {endpoint_url}: {e}")
    return []
