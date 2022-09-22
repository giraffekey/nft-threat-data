# nft-threat-data

Collection, analysis and visualization of NFT threat detection datasets.

## Collection

First create a Mainnet Infura endpoint:

`export INFURA_MAINNET_ENDPOINT=https://mainnet.infura.io/v3/[key]`

Run data collection script:

`python3 collect_data.py`

Compile data snapshots to single dataset file:

`python3 compile_data.py`
