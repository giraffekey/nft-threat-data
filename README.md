# nft-threat-data

Collection, analysis and visualization of NFT threat detection datasets.

## Installation

`pip3 install -r requirements.txt`

## Collection

First create a Mainnet Infura endpoint:

`export INFURA_MAINNET_ENDPOINT=https://mainnet.infura.io/v3/[key]`

Run data collection script:

`python3 collect_data.py`

Compile data snapshots to single dataset file:

`python3 compile_data.py`
