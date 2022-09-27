# nft-threat-data

Collection, analysis and visualization of NFT threat detection datasets.

## Installation

`pip3 install -r requirements.txt`

## Collection

### Steps

First create a Mainnet Infura endpoint:

`export INFURA_MAINNET_ENDPOINT=https://mainnet.infura.io/v3/[key]`

Run data collection script:

`python3 collect_data.py`

Compile data snapshots to single dataset file:

`python3 compile_data.py`

### Info

The data collection script queries events from multiple smart contracts to find unique NFT contract addresses. Once a list of new addresses is discovered, the Forta API is queried for alerts for each address and the data is processed and saved in snapshot CSV files.
