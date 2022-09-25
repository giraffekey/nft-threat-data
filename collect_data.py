import atexit
import csv
from datetime import datetime
import json
import math
import os

import asyncio
import backoff

from gql import gql, Client
from gql.transport.aiohttp import AIOHTTPTransport
from gql.transport.exceptions import TransportQueryError

import web3
from web3 import Web3

import lmdb
from tqdm import tqdm


FIELDNAMES = ["asset", "platform", "alert_id", "severity", "name", "description"]

BOTS = [
  "0x2e51c6a89c2dccc16a813bb0c3bf3bbfe94414b6a0ea3fc650ad2a59e148f3c8",
  "0x20d57d727a2d7bf4b447d1952d7ea44efeda0920e45e779d298d5385f3b36cfa",
  "0x9a8134e4a061e3c0098fd14f8d54c2391fb9118ff403e4b2c79faf6390f0e518",
  "0x0e82982faa7878af3fad8ddf5042762a3b78d8949da2e301f1adfedc973f25ea",
  "0x8badbf2ad65abc3df5b1d9cc388e419d9255ef999fb69aac6bf395646cf01c14",
  "0x0f21668ebd017888e7ee7dd46e9119bdd2bc7f48dbabc375d96c9b415267534c",
  "0x20d0cd9432c7e15cb625097a718c15cc07f463b5252e3c36ae23acb7ef98d54e",
  "0x457aa09ca38d60410c8ffa1761f535f23959195a56c9b82e0207801e86b34d99",
  "0x6aa2012744a3eb210fc4e4b794d9df59684d36d502fd9efe509a867d0efa5127",
  "0x617c356a4ad4b755035ef8024a87d36d895ee3cb0864e7ce9b3cf694dd80c82a",
  "0x4c7e56a9a753e29ca92bd57dd593bdab0c03e762bdd04e2bc578cb82b842c1f3",
]


class Wyvern:
  def __init__(self, w3, db):
    self.abi = [{"constant":True,"inputs":[],"name":"name","outputs":[{"name":"","type":"string"}],"payable":False,"stateMutability":"view","type":"function"},{"constant":True,"inputs":[],"name":"tokenTransferProxy","outputs":[{"name":"","type":"address"}],"payable":False,"stateMutability":"view","type":"function"},{"constant":True,"inputs":[{"name":"target","type":"address"},{"name":"calldata","type":"bytes"},{"name":"extradata","type":"bytes"}],"name":"staticCall","outputs":[{"name":"result","type":"bool"}],"payable":False,"stateMutability":"view","type":"function"},{"constant":False,"inputs":[{"name":"newMinimumMakerProtocolFee","type":"uint256"}],"name":"changeMinimumMakerProtocolFee","outputs":[],"payable":False,"stateMutability":"nonpayable","type":"function"},{"constant":False,"inputs":[{"name":"newMinimumTakerProtocolFee","type":"uint256"}],"name":"changeMinimumTakerProtocolFee","outputs":[],"payable":False,"stateMutability":"nonpayable","type":"function"},{"constant":True,"inputs":[{"name":"array","type":"bytes"},{"name":"desired","type":"bytes"},{"name":"mask","type":"bytes"}],"name":"guardedArrayReplace","outputs":[{"name":"","type":"bytes"}],"payable":False,"stateMutability":"pure","type":"function"},{"constant":True,"inputs":[],"name":"minimumTakerProtocolFee","outputs":[{"name":"","type":"uint256"}],"payable":False,"stateMutability":"view","type":"function"},{"constant":True,"inputs":[],"name":"codename","outputs":[{"name":"","type":"string"}],"payable":False,"stateMutability":"view","type":"function"},{"constant":True,"inputs":[],"name":"DOMAIN_SEPARATOR","outputs":[{"name":"","type":"bytes32"}],"payable":False,"stateMutability":"view","type":"function"},{"constant":True,"inputs":[{"name":"addrs","type":"address[7]"},{"name":"uints","type":"uint256[9]"},{"name":"feeMethod","type":"uint8"},{"name":"side","type":"uint8"},{"name":"saleKind","type":"uint8"},{"name":"howToCall","type":"uint8"},{"name":"calldata","type":"bytes"},{"name":"replacementPattern","type":"bytes"},{"name":"staticExtradata","type":"bytes"}],"name":"calculateCurrentPrice_","outputs":[{"name":"","type":"uint256"}],"payable":False,"stateMutability":"view","type":"function"},{"constant":False,"inputs":[{"name":"newProtocolFeeRecipient","type":"address"}],"name":"changeProtocolFeeRecipient","outputs":[],"payable":False,"stateMutability":"nonpayable","type":"function"},{"constant":True,"inputs":[],"name":"version","outputs":[{"name":"","type":"string"}],"payable":False,"stateMutability":"view","type":"function"},{"constant":True,"inputs":[{"name":"buyCalldata","type":"bytes"},{"name":"buyReplacementPattern","type":"bytes"},{"name":"sellCalldata","type":"bytes"},{"name":"sellReplacementPattern","type":"bytes"}],"name":"orderCalldataCanMatch","outputs":[{"name":"","type":"bool"}],"payable":False,"stateMutability":"pure","type":"function"},{"constant":True,"inputs":[{"name":"addrs","type":"address[7]"},{"name":"uints","type":"uint256[9]"},{"name":"feeMethod","type":"uint8"},{"name":"side","type":"uint8"},{"name":"saleKind","type":"uint8"},{"name":"howToCall","type":"uint8"},{"name":"calldata","type":"bytes"},{"name":"replacementPattern","type":"bytes"},{"name":"staticExtradata","type":"bytes"},{"name":"v","type":"uint8"},{"name":"r","type":"bytes32"},{"name":"s","type":"bytes32"}],"name":"validateOrder_","outputs":[{"name":"","type":"bool"}],"payable":False,"stateMutability":"view","type":"function"},{"constant":False,"inputs":[],"name":"incrementNonce","outputs":[],"payable":False,"stateMutability":"nonpayable","type":"function"},{"constant":True,"inputs":[{"name":"side","type":"uint8"},{"name":"saleKind","type":"uint8"},{"name":"basePrice","type":"uint256"},{"name":"extra","type":"uint256"},{"name":"listingTime","type":"uint256"},{"name":"expirationTime","type":"uint256"}],"name":"calculateFinalPrice","outputs":[{"name":"","type":"uint256"}],"payable":False,"stateMutability":"view","type":"function"},{"constant":True,"inputs":[],"name":"protocolFeeRecipient","outputs":[{"name":"","type":"address"}],"payable":False,"stateMutability":"view","type":"function"},{"constant":False,"inputs":[],"name":"renounceOwnership","outputs":[],"payable":False,"stateMutability":"nonpayable","type":"function"},{"constant":True,"inputs":[{"name":"addrs","type":"address[7]"},{"name":"uints","type":"uint256[9]"},{"name":"feeMethod","type":"uint8"},{"name":"side","type":"uint8"},{"name":"saleKind","type":"uint8"},{"name":"howToCall","type":"uint8"},{"name":"calldata","type":"bytes"},{"name":"replacementPattern","type":"bytes"},{"name":"staticExtradata","type":"bytes"}],"name":"hashOrder_","outputs":[{"name":"","type":"bytes32"}],"payable":False,"stateMutability":"view","type":"function"},{"constant":True,"inputs":[{"name":"addrs","type":"address[14]"},{"name":"uints","type":"uint256[18]"},{"name":"feeMethodsSidesKindsHowToCalls","type":"uint8[8]"},{"name":"calldataBuy","type":"bytes"},{"name":"calldataSell","type":"bytes"},{"name":"replacementPatternBuy","type":"bytes"},{"name":"replacementPatternSell","type":"bytes"},{"name":"staticExtradataBuy","type":"bytes"},{"name":"staticExtradataSell","type":"bytes"}],"name":"ordersCanMatch_","outputs":[{"name":"","type":"bool"}],"payable":False,"stateMutability":"view","type":"function"},{"constant":False,"inputs":[{"name":"addrs","type":"address[7]"},{"name":"uints","type":"uint256[9]"},{"name":"feeMethod","type":"uint8"},{"name":"side","type":"uint8"},{"name":"saleKind","type":"uint8"},{"name":"howToCall","type":"uint8"},{"name":"calldata","type":"bytes"},{"name":"replacementPattern","type":"bytes"},{"name":"staticExtradata","type":"bytes"},{"name":"orderbookInclusionDesired","type":"bool"}],"name":"approveOrder_","outputs":[],"payable":False,"stateMutability":"nonpayable","type":"function"},{"constant":True,"inputs":[],"name":"registry","outputs":[{"name":"","type":"address"}],"payable":False,"stateMutability":"view","type":"function"},{"constant":True,"inputs":[],"name":"minimumMakerProtocolFee","outputs":[{"name":"","type":"uint256"}],"payable":False,"stateMutability":"view","type":"function"},{"constant":True,"inputs":[{"name":"addrs","type":"address[7]"},{"name":"uints","type":"uint256[9]"},{"name":"feeMethod","type":"uint8"},{"name":"side","type":"uint8"},{"name":"saleKind","type":"uint8"},{"name":"howToCall","type":"uint8"},{"name":"calldata","type":"bytes"},{"name":"replacementPattern","type":"bytes"},{"name":"staticExtradata","type":"bytes"}],"name":"hashToSign_","outputs":[{"name":"","type":"bytes32"}],"payable":False,"stateMutability":"view","type":"function"},{"constant":True,"inputs":[{"name":"","type":"address"}],"name":"nonces","outputs":[{"name":"","type":"uint256"}],"payable":False,"stateMutability":"view","type":"function"},{"constant":True,"inputs":[{"name":"","type":"bytes32"}],"name":"cancelledOrFinalized","outputs":[{"name":"","type":"bool"}],"payable":False,"stateMutability":"view","type":"function"},{"constant":True,"inputs":[],"name":"owner","outputs":[{"name":"","type":"address"}],"payable":False,"stateMutability":"view","type":"function"},{"constant":True,"inputs":[],"name":"exchangeToken","outputs":[{"name":"","type":"address"}],"payable":False,"stateMutability":"view","type":"function"},{"constant":False,"inputs":[{"name":"addrs","type":"address[7]"},{"name":"uints","type":"uint256[9]"},{"name":"feeMethod","type":"uint8"},{"name":"side","type":"uint8"},{"name":"saleKind","type":"uint8"},{"name":"howToCall","type":"uint8"},{"name":"calldata","type":"bytes"},{"name":"replacementPattern","type":"bytes"},{"name":"staticExtradata","type":"bytes"},{"name":"v","type":"uint8"},{"name":"r","type":"bytes32"},{"name":"s","type":"bytes32"}],"name":"cancelOrder_","outputs":[],"payable":False,"stateMutability":"nonpayable","type":"function"},{"constant":False,"inputs":[{"name":"addrs","type":"address[14]"},{"name":"uints","type":"uint256[18]"},{"name":"feeMethodsSidesKindsHowToCalls","type":"uint8[8]"},{"name":"calldataBuy","type":"bytes"},{"name":"calldataSell","type":"bytes"},{"name":"replacementPatternBuy","type":"bytes"},{"name":"replacementPatternSell","type":"bytes"},{"name":"staticExtradataBuy","type":"bytes"},{"name":"staticExtradataSell","type":"bytes"},{"name":"vs","type":"uint8[2]"},{"name":"rssMetadata","type":"bytes32[5]"}],"name":"atomicMatch_","outputs":[],"payable":True,"stateMutability":"payable","type":"function"},{"constant":True,"inputs":[{"name":"addrs","type":"address[7]"},{"name":"uints","type":"uint256[9]"},{"name":"feeMethod","type":"uint8"},{"name":"side","type":"uint8"},{"name":"saleKind","type":"uint8"},{"name":"howToCall","type":"uint8"},{"name":"calldata","type":"bytes"},{"name":"replacementPattern","type":"bytes"},{"name":"staticExtradata","type":"bytes"}],"name":"validateOrderParameters_","outputs":[{"name":"","type":"bool"}],"payable":False,"stateMutability":"view","type":"function"},{"constant":True,"inputs":[],"name":"INVERSE_BASIS_POINT","outputs":[{"name":"","type":"uint256"}],"payable":False,"stateMutability":"view","type":"function"},{"constant":True,"inputs":[{"name":"addrs","type":"address[14]"},{"name":"uints","type":"uint256[18]"},{"name":"feeMethodsSidesKindsHowToCalls","type":"uint8[8]"},{"name":"calldataBuy","type":"bytes"},{"name":"calldataSell","type":"bytes"},{"name":"replacementPatternBuy","type":"bytes"},{"name":"replacementPatternSell","type":"bytes"},{"name":"staticExtradataBuy","type":"bytes"},{"name":"staticExtradataSell","type":"bytes"}],"name":"calculateMatchPrice_","outputs":[{"name":"","type":"uint256"}],"payable":False,"stateMutability":"view","type":"function"},{"constant":True,"inputs":[{"name":"hash","type":"bytes32"}],"name":"approvedOrders","outputs":[{"name":"approved","type":"bool"}],"payable":False,"stateMutability":"view","type":"function"},{"constant":False,"inputs":[{"name":"newOwner","type":"address"}],"name":"transferOwnership","outputs":[],"payable":False,"stateMutability":"nonpayable","type":"function"},{"constant":False,"inputs":[{"name":"addrs","type":"address[7]"},{"name":"uints","type":"uint256[9]"},{"name":"feeMethod","type":"uint8"},{"name":"side","type":"uint8"},{"name":"saleKind","type":"uint8"},{"name":"howToCall","type":"uint8"},{"name":"calldata","type":"bytes"},{"name":"replacementPattern","type":"bytes"},{"name":"staticExtradata","type":"bytes"},{"name":"v","type":"uint8"},{"name":"r","type":"bytes32"},{"name":"s","type":"bytes32"},{"name":"nonce","type":"uint256"}],"name":"cancelOrderWithNonce_","outputs":[],"payable":False,"stateMutability":"nonpayable","type":"function"},{"inputs":[{"name":"registryAddress","type":"address"},{"name":"tokenTransferProxyAddress","type":"address"},{"name":"tokenAddress","type":"address"},{"name":"protocolFeeAddress","type":"address"}],"payable":False,"stateMutability":"nonpayable","type":"constructor"},{"anonymous":False,"inputs":[{"indexed":True,"name":"hash","type":"bytes32"},{"indexed":False,"name":"exchange","type":"address"},{"indexed":True,"name":"maker","type":"address"},{"indexed":False,"name":"taker","type":"address"},{"indexed":False,"name":"makerRelayerFee","type":"uint256"},{"indexed":False,"name":"takerRelayerFee","type":"uint256"},{"indexed":False,"name":"makerProtocolFee","type":"uint256"},{"indexed":False,"name":"takerProtocolFee","type":"uint256"},{"indexed":True,"name":"feeRecipient","type":"address"},{"indexed":False,"name":"feeMethod","type":"uint8"},{"indexed":False,"name":"side","type":"uint8"},{"indexed":False,"name":"saleKind","type":"uint8"},{"indexed":False,"name":"target","type":"address"}],"name":"OrderApprovedPartOne","type":"event"},{"anonymous":False,"inputs":[{"indexed":True,"name":"hash","type":"bytes32"},{"indexed":False,"name":"howToCall","type":"uint8"},{"indexed":False,"name":"calldata","type":"bytes"},{"indexed":False,"name":"replacementPattern","type":"bytes"},{"indexed":False,"name":"staticTarget","type":"address"},{"indexed":False,"name":"staticExtradata","type":"bytes"},{"indexed":False,"name":"paymentToken","type":"address"},{"indexed":False,"name":"basePrice","type":"uint256"},{"indexed":False,"name":"extra","type":"uint256"},{"indexed":False,"name":"listingTime","type":"uint256"},{"indexed":False,"name":"expirationTime","type":"uint256"},{"indexed":False,"name":"salt","type":"uint256"},{"indexed":False,"name":"orderbookInclusionDesired","type":"bool"}],"name":"OrderApprovedPartTwo","type":"event"},{"anonymous":False,"inputs":[{"indexed":True,"name":"hash","type":"bytes32"}],"name":"OrderCancelled","type":"event"},{"anonymous":False,"inputs":[{"indexed":False,"name":"buyHash","type":"bytes32"},{"indexed":False,"name":"sellHash","type":"bytes32"},{"indexed":True,"name":"maker","type":"address"},{"indexed":True,"name":"taker","type":"address"},{"indexed":False,"name":"price","type":"uint256"},{"indexed":True,"name":"metadata","type":"bytes32"}],"name":"OrdersMatched","type":"event"},{"anonymous":False,"inputs":[{"indexed":True,"name":"maker","type":"address"},{"indexed":False,"name":"newNonce","type":"uint256"}],"name":"NonceIncremented","type":"event"},{"anonymous":False,"inputs":[{"indexed":True,"name":"previousOwner","type":"address"}],"name":"OwnershipRenounced","type":"event"},{"anonymous":False,"inputs":[{"indexed":True,"name":"previousOwner","type":"address"},{"indexed":True,"name":"newOwner","type":"address"}],"name":"OwnershipTransferred","type":"event"}]
    self.contract = w3.eth.contract(address="0x7f268357A8c2552623316e2562D90e642bB538E5", abi=self.abi)
    self.poll_filter = self.contract.events.OrdersMatched.createFilter(fromBlock="latest")

    self.db = db
    with db.begin() as txn:
      self.block = json.loads(txn.get(b"wyvern_block"))

    self.start_block = w3.eth.block_number
    self.i = 0
    self.step = 10_000
    self.crawl_finished = False

  def extract_addresses(self, entries):
    return entries

  async def find_addresses(self):
    if self.crawl_finished:
      entries = []
    else:
      fromBlock = self.block + self.i * self.step
      toBlock = self.block + (self.i + 1) * self.step
      if toBlock > self.start_block:
        toBlock = self.start_block

      # with self.db.begin(write=True) as txn:
      #   txn.put(b"wyvern_block", json.dumps(fromBlock).encode())

      try:
        crawl_filter = self.contract.events.OrdersMatched.createFilter(fromBlock=fromBlock, toBlock=toBlock)
        entries = crawl_filter.get_all_entries()
      except ValueError as e:
        if "message" in e.args[0] and e.args[0]["message"] == "query returned more than 10000 results":
          self.step = self.step * 4 // 5
          return await self.find_addresses()
        else:
          raise e

      if toBlock == self.start_block:
        self.crawl_finished = True

      self.i += 1

    entries.extend(self.poll_filter.get_new_entries())

    return self.extract_addresses(entries)

  async def sleep(self):
    if self.crawl_finished:
      await asyncio.sleep(10)
    else:
      await asyncio.sleep(1)


class Seaport:
  def __init__(self, w3, db):
    self.abi = [{"inputs":[{"internalType":"address","name":"conduitController","type":"address"}],"stateMutability":"nonpayable","type":"constructor"},{"inputs":[],"name":"BadContractSignature","type":"error"},{"inputs":[],"name":"BadFraction","type":"error"},{"inputs":[{"internalType":"address","name":"token","type":"address"},{"internalType":"address","name":"from","type":"address"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"}],"name":"BadReturnValueFromERC20OnTransfer","type":"error"},{"inputs":[{"internalType":"uint8","name":"v","type":"uint8"}],"name":"BadSignatureV","type":"error"},{"inputs":[],"name":"ConsiderationCriteriaResolverOutOfRange","type":"error"},{"inputs":[{"internalType":"uint256","name":"orderIndex","type":"uint256"},{"internalType":"uint256","name":"considerationIndex","type":"uint256"},{"internalType":"uint256","name":"shortfallAmount","type":"uint256"}],"name":"ConsiderationNotMet","type":"error"},{"inputs":[],"name":"CriteriaNotEnabledForItem","type":"error"},{"inputs":[{"internalType":"address","name":"token","type":"address"},{"internalType":"address","name":"from","type":"address"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256[]","name":"identifiers","type":"uint256[]"},{"internalType":"uint256[]","name":"amounts","type":"uint256[]"}],"name":"ERC1155BatchTransferGenericFailure","type":"error"},{"inputs":[{"internalType":"address","name":"account","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"}],"name":"EtherTransferGenericFailure","type":"error"},{"inputs":[],"name":"InexactFraction","type":"error"},{"inputs":[],"name":"InsufficientEtherSupplied","type":"error"},{"inputs":[],"name":"Invalid1155BatchTransferEncoding","type":"error"},{"inputs":[],"name":"InvalidBasicOrderParameterEncoding","type":"error"},{"inputs":[{"internalType":"address","name":"conduit","type":"address"}],"name":"InvalidCallToConduit","type":"error"},{"inputs":[],"name":"InvalidCanceller","type":"error"},{"inputs":[{"internalType":"bytes32","name":"conduitKey","type":"bytes32"},{"internalType":"address","name":"conduit","type":"address"}],"name":"InvalidConduit","type":"error"},{"inputs":[],"name":"InvalidERC721TransferAmount","type":"error"},{"inputs":[],"name":"InvalidFulfillmentComponentData","type":"error"},{"inputs":[{"internalType":"uint256","name":"value","type":"uint256"}],"name":"InvalidMsgValue","type":"error"},{"inputs":[],"name":"InvalidNativeOfferItem","type":"error"},{"inputs":[],"name":"InvalidProof","type":"error"},{"inputs":[{"internalType":"bytes32","name":"orderHash","type":"bytes32"}],"name":"InvalidRestrictedOrder","type":"error"},{"inputs":[],"name":"InvalidSignature","type":"error"},{"inputs":[],"name":"InvalidSigner","type":"error"},{"inputs":[],"name":"InvalidTime","type":"error"},{"inputs":[],"name":"MismatchedFulfillmentOfferAndConsiderationComponents","type":"error"},{"inputs":[{"internalType":"enum Side","name":"side","type":"uint8"}],"name":"MissingFulfillmentComponentOnAggregation","type":"error"},{"inputs":[],"name":"MissingItemAmount","type":"error"},{"inputs":[],"name":"MissingOriginalConsiderationItems","type":"error"},{"inputs":[{"internalType":"address","name":"account","type":"address"}],"name":"NoContract","type":"error"},{"inputs":[],"name":"NoReentrantCalls","type":"error"},{"inputs":[],"name":"NoSpecifiedOrdersAvailable","type":"error"},{"inputs":[],"name":"OfferAndConsiderationRequiredOnFulfillment","type":"error"},{"inputs":[],"name":"OfferCriteriaResolverOutOfRange","type":"error"},{"inputs":[{"internalType":"bytes32","name":"orderHash","type":"bytes32"}],"name":"OrderAlreadyFilled","type":"error"},{"inputs":[],"name":"OrderCriteriaResolverOutOfRange","type":"error"},{"inputs":[{"internalType":"bytes32","name":"orderHash","type":"bytes32"}],"name":"OrderIsCancelled","type":"error"},{"inputs":[{"internalType":"bytes32","name":"orderHash","type":"bytes32"}],"name":"OrderPartiallyFilled","type":"error"},{"inputs":[],"name":"PartialFillsNotEnabledForOrder","type":"error"},{"inputs":[{"internalType":"address","name":"token","type":"address"},{"internalType":"address","name":"from","type":"address"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"identifier","type":"uint256"},{"internalType":"uint256","name":"amount","type":"uint256"}],"name":"TokenTransferGenericFailure","type":"error"},{"inputs":[],"name":"UnresolvedConsiderationCriteria","type":"error"},{"inputs":[],"name":"UnresolvedOfferCriteria","type":"error"},{"inputs":[],"name":"UnusedItemParameters","type":"error"},{"anonymous":False,"inputs":[{"indexed":False,"internalType":"uint256","name":"newCounter","type":"uint256"},{"indexed":True,"internalType":"address","name":"offerer","type":"address"}],"name":"CounterIncremented","type":"event"},{"anonymous":False,"inputs":[{"indexed":False,"internalType":"bytes32","name":"orderHash","type":"bytes32"},{"indexed":True,"internalType":"address","name":"offerer","type":"address"},{"indexed":True,"internalType":"address","name":"zone","type":"address"}],"name":"OrderCancelled","type":"event"},{"anonymous":False,"inputs":[{"indexed":False,"internalType":"bytes32","name":"orderHash","type":"bytes32"},{"indexed":True,"internalType":"address","name":"offerer","type":"address"},{"indexed":True,"internalType":"address","name":"zone","type":"address"},{"indexed":False,"internalType":"address","name":"recipient","type":"address"},{"components":[{"internalType":"enum ItemType","name":"itemType","type":"uint8"},{"internalType":"address","name":"token","type":"address"},{"internalType":"uint256","name":"identifier","type":"uint256"},{"internalType":"uint256","name":"amount","type":"uint256"}],"indexed":False,"internalType":"struct SpentItem[]","name":"offer","type":"tuple[]"},{"components":[{"internalType":"enum ItemType","name":"itemType","type":"uint8"},{"internalType":"address","name":"token","type":"address"},{"internalType":"uint256","name":"identifier","type":"uint256"},{"internalType":"uint256","name":"amount","type":"uint256"},{"internalType":"address payable","name":"recipient","type":"address"}],"indexed":False,"internalType":"struct ReceivedItem[]","name":"consideration","type":"tuple[]"}],"name":"OrderFulfilled","type":"event"},{"anonymous":False,"inputs":[{"indexed":False,"internalType":"bytes32","name":"orderHash","type":"bytes32"},{"indexed":True,"internalType":"address","name":"offerer","type":"address"},{"indexed":True,"internalType":"address","name":"zone","type":"address"}],"name":"OrderValidated","type":"event"},{"inputs":[{"components":[{"internalType":"address","name":"offerer","type":"address"},{"internalType":"address","name":"zone","type":"address"},{"components":[{"internalType":"enum ItemType","name":"itemType","type":"uint8"},{"internalType":"address","name":"token","type":"address"},{"internalType":"uint256","name":"identifierOrCriteria","type":"uint256"},{"internalType":"uint256","name":"startAmount","type":"uint256"},{"internalType":"uint256","name":"endAmount","type":"uint256"}],"internalType":"struct OfferItem[]","name":"offer","type":"tuple[]"},{"components":[{"internalType":"enum ItemType","name":"itemType","type":"uint8"},{"internalType":"address","name":"token","type":"address"},{"internalType":"uint256","name":"identifierOrCriteria","type":"uint256"},{"internalType":"uint256","name":"startAmount","type":"uint256"},{"internalType":"uint256","name":"endAmount","type":"uint256"},{"internalType":"address payable","name":"recipient","type":"address"}],"internalType":"struct ConsiderationItem[]","name":"consideration","type":"tuple[]"},{"internalType":"enum OrderType","name":"orderType","type":"uint8"},{"internalType":"uint256","name":"startTime","type":"uint256"},{"internalType":"uint256","name":"endTime","type":"uint256"},{"internalType":"bytes32","name":"zoneHash","type":"bytes32"},{"internalType":"uint256","name":"salt","type":"uint256"},{"internalType":"bytes32","name":"conduitKey","type":"bytes32"},{"internalType":"uint256","name":"counter","type":"uint256"}],"internalType":"struct OrderComponents[]","name":"orders","type":"tuple[]"}],"name":"cancel","outputs":[{"internalType":"bool","name":"cancelled","type":"bool"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"components":[{"components":[{"internalType":"address","name":"offerer","type":"address"},{"internalType":"address","name":"zone","type":"address"},{"components":[{"internalType":"enum ItemType","name":"itemType","type":"uint8"},{"internalType":"address","name":"token","type":"address"},{"internalType":"uint256","name":"identifierOrCriteria","type":"uint256"},{"internalType":"uint256","name":"startAmount","type":"uint256"},{"internalType":"uint256","name":"endAmount","type":"uint256"}],"internalType":"struct OfferItem[]","name":"offer","type":"tuple[]"},{"components":[{"internalType":"enum ItemType","name":"itemType","type":"uint8"},{"internalType":"address","name":"token","type":"address"},{"internalType":"uint256","name":"identifierOrCriteria","type":"uint256"},{"internalType":"uint256","name":"startAmount","type":"uint256"},{"internalType":"uint256","name":"endAmount","type":"uint256"},{"internalType":"address payable","name":"recipient","type":"address"}],"internalType":"struct ConsiderationItem[]","name":"consideration","type":"tuple[]"},{"internalType":"enum OrderType","name":"orderType","type":"uint8"},{"internalType":"uint256","name":"startTime","type":"uint256"},{"internalType":"uint256","name":"endTime","type":"uint256"},{"internalType":"bytes32","name":"zoneHash","type":"bytes32"},{"internalType":"uint256","name":"salt","type":"uint256"},{"internalType":"bytes32","name":"conduitKey","type":"bytes32"},{"internalType":"uint256","name":"totalOriginalConsiderationItems","type":"uint256"}],"internalType":"struct OrderParameters","name":"parameters","type":"tuple"},{"internalType":"uint120","name":"numerator","type":"uint120"},{"internalType":"uint120","name":"denominator","type":"uint120"},{"internalType":"bytes","name":"signature","type":"bytes"},{"internalType":"bytes","name":"extraData","type":"bytes"}],"internalType":"struct AdvancedOrder","name":"advancedOrder","type":"tuple"},{"components":[{"internalType":"uint256","name":"orderIndex","type":"uint256"},{"internalType":"enum Side","name":"side","type":"uint8"},{"internalType":"uint256","name":"index","type":"uint256"},{"internalType":"uint256","name":"identifier","type":"uint256"},{"internalType":"bytes32[]","name":"criteriaProof","type":"bytes32[]"}],"internalType":"struct CriteriaResolver[]","name":"criteriaResolvers","type":"tuple[]"},{"internalType":"bytes32","name":"fulfillerConduitKey","type":"bytes32"},{"internalType":"address","name":"recipient","type":"address"}],"name":"fulfillAdvancedOrder","outputs":[{"internalType":"bool","name":"fulfilled","type":"bool"}],"stateMutability":"payable","type":"function"},{"inputs":[{"components":[{"components":[{"internalType":"address","name":"offerer","type":"address"},{"internalType":"address","name":"zone","type":"address"},{"components":[{"internalType":"enum ItemType","name":"itemType","type":"uint8"},{"internalType":"address","name":"token","type":"address"},{"internalType":"uint256","name":"identifierOrCriteria","type":"uint256"},{"internalType":"uint256","name":"startAmount","type":"uint256"},{"internalType":"uint256","name":"endAmount","type":"uint256"}],"internalType":"struct OfferItem[]","name":"offer","type":"tuple[]"},{"components":[{"internalType":"enum ItemType","name":"itemType","type":"uint8"},{"internalType":"address","name":"token","type":"address"},{"internalType":"uint256","name":"identifierOrCriteria","type":"uint256"},{"internalType":"uint256","name":"startAmount","type":"uint256"},{"internalType":"uint256","name":"endAmount","type":"uint256"},{"internalType":"address payable","name":"recipient","type":"address"}],"internalType":"struct ConsiderationItem[]","name":"consideration","type":"tuple[]"},{"internalType":"enum OrderType","name":"orderType","type":"uint8"},{"internalType":"uint256","name":"startTime","type":"uint256"},{"internalType":"uint256","name":"endTime","type":"uint256"},{"internalType":"bytes32","name":"zoneHash","type":"bytes32"},{"internalType":"uint256","name":"salt","type":"uint256"},{"internalType":"bytes32","name":"conduitKey","type":"bytes32"},{"internalType":"uint256","name":"totalOriginalConsiderationItems","type":"uint256"}],"internalType":"struct OrderParameters","name":"parameters","type":"tuple"},{"internalType":"uint120","name":"numerator","type":"uint120"},{"internalType":"uint120","name":"denominator","type":"uint120"},{"internalType":"bytes","name":"signature","type":"bytes"},{"internalType":"bytes","name":"extraData","type":"bytes"}],"internalType":"struct AdvancedOrder[]","name":"advancedOrders","type":"tuple[]"},{"components":[{"internalType":"uint256","name":"orderIndex","type":"uint256"},{"internalType":"enum Side","name":"side","type":"uint8"},{"internalType":"uint256","name":"index","type":"uint256"},{"internalType":"uint256","name":"identifier","type":"uint256"},{"internalType":"bytes32[]","name":"criteriaProof","type":"bytes32[]"}],"internalType":"struct CriteriaResolver[]","name":"criteriaResolvers","type":"tuple[]"},{"components":[{"internalType":"uint256","name":"orderIndex","type":"uint256"},{"internalType":"uint256","name":"itemIndex","type":"uint256"}],"internalType":"struct FulfillmentComponent[][]","name":"offerFulfillments","type":"tuple[][]"},{"components":[{"internalType":"uint256","name":"orderIndex","type":"uint256"},{"internalType":"uint256","name":"itemIndex","type":"uint256"}],"internalType":"struct FulfillmentComponent[][]","name":"considerationFulfillments","type":"tuple[][]"},{"internalType":"bytes32","name":"fulfillerConduitKey","type":"bytes32"},{"internalType":"address","name":"recipient","type":"address"},{"internalType":"uint256","name":"maximumFulfilled","type":"uint256"}],"name":"fulfillAvailableAdvancedOrders","outputs":[{"internalType":"bool[]","name":"availableOrders","type":"bool[]"},{"components":[{"components":[{"internalType":"enum ItemType","name":"itemType","type":"uint8"},{"internalType":"address","name":"token","type":"address"},{"internalType":"uint256","name":"identifier","type":"uint256"},{"internalType":"uint256","name":"amount","type":"uint256"},{"internalType":"address payable","name":"recipient","type":"address"}],"internalType":"struct ReceivedItem","name":"item","type":"tuple"},{"internalType":"address","name":"offerer","type":"address"},{"internalType":"bytes32","name":"conduitKey","type":"bytes32"}],"internalType":"struct Execution[]","name":"executions","type":"tuple[]"}],"stateMutability":"payable","type":"function"},{"inputs":[{"components":[{"components":[{"internalType":"address","name":"offerer","type":"address"},{"internalType":"address","name":"zone","type":"address"},{"components":[{"internalType":"enum ItemType","name":"itemType","type":"uint8"},{"internalType":"address","name":"token","type":"address"},{"internalType":"uint256","name":"identifierOrCriteria","type":"uint256"},{"internalType":"uint256","name":"startAmount","type":"uint256"},{"internalType":"uint256","name":"endAmount","type":"uint256"}],"internalType":"struct OfferItem[]","name":"offer","type":"tuple[]"},{"components":[{"internalType":"enum ItemType","name":"itemType","type":"uint8"},{"internalType":"address","name":"token","type":"address"},{"internalType":"uint256","name":"identifierOrCriteria","type":"uint256"},{"internalType":"uint256","name":"startAmount","type":"uint256"},{"internalType":"uint256","name":"endAmount","type":"uint256"},{"internalType":"address payable","name":"recipient","type":"address"}],"internalType":"struct ConsiderationItem[]","name":"consideration","type":"tuple[]"},{"internalType":"enum OrderType","name":"orderType","type":"uint8"},{"internalType":"uint256","name":"startTime","type":"uint256"},{"internalType":"uint256","name":"endTime","type":"uint256"},{"internalType":"bytes32","name":"zoneHash","type":"bytes32"},{"internalType":"uint256","name":"salt","type":"uint256"},{"internalType":"bytes32","name":"conduitKey","type":"bytes32"},{"internalType":"uint256","name":"totalOriginalConsiderationItems","type":"uint256"}],"internalType":"struct OrderParameters","name":"parameters","type":"tuple"},{"internalType":"bytes","name":"signature","type":"bytes"}],"internalType":"struct Order[]","name":"orders","type":"tuple[]"},{"components":[{"internalType":"uint256","name":"orderIndex","type":"uint256"},{"internalType":"uint256","name":"itemIndex","type":"uint256"}],"internalType":"struct FulfillmentComponent[][]","name":"offerFulfillments","type":"tuple[][]"},{"components":[{"internalType":"uint256","name":"orderIndex","type":"uint256"},{"internalType":"uint256","name":"itemIndex","type":"uint256"}],"internalType":"struct FulfillmentComponent[][]","name":"considerationFulfillments","type":"tuple[][]"},{"internalType":"bytes32","name":"fulfillerConduitKey","type":"bytes32"},{"internalType":"uint256","name":"maximumFulfilled","type":"uint256"}],"name":"fulfillAvailableOrders","outputs":[{"internalType":"bool[]","name":"availableOrders","type":"bool[]"},{"components":[{"components":[{"internalType":"enum ItemType","name":"itemType","type":"uint8"},{"internalType":"address","name":"token","type":"address"},{"internalType":"uint256","name":"identifier","type":"uint256"},{"internalType":"uint256","name":"amount","type":"uint256"},{"internalType":"address payable","name":"recipient","type":"address"}],"internalType":"struct ReceivedItem","name":"item","type":"tuple"},{"internalType":"address","name":"offerer","type":"address"},{"internalType":"bytes32","name":"conduitKey","type":"bytes32"}],"internalType":"struct Execution[]","name":"executions","type":"tuple[]"}],"stateMutability":"payable","type":"function"},{"inputs":[{"components":[{"internalType":"address","name":"considerationToken","type":"address"},{"internalType":"uint256","name":"considerationIdentifier","type":"uint256"},{"internalType":"uint256","name":"considerationAmount","type":"uint256"},{"internalType":"address payable","name":"offerer","type":"address"},{"internalType":"address","name":"zone","type":"address"},{"internalType":"address","name":"offerToken","type":"address"},{"internalType":"uint256","name":"offerIdentifier","type":"uint256"},{"internalType":"uint256","name":"offerAmount","type":"uint256"},{"internalType":"enum BasicOrderType","name":"basicOrderType","type":"uint8"},{"internalType":"uint256","name":"startTime","type":"uint256"},{"internalType":"uint256","name":"endTime","type":"uint256"},{"internalType":"bytes32","name":"zoneHash","type":"bytes32"},{"internalType":"uint256","name":"salt","type":"uint256"},{"internalType":"bytes32","name":"offererConduitKey","type":"bytes32"},{"internalType":"bytes32","name":"fulfillerConduitKey","type":"bytes32"},{"internalType":"uint256","name":"totalOriginalAdditionalRecipients","type":"uint256"},{"components":[{"internalType":"uint256","name":"amount","type":"uint256"},{"internalType":"address payable","name":"recipient","type":"address"}],"internalType":"struct AdditionalRecipient[]","name":"additionalRecipients","type":"tuple[]"},{"internalType":"bytes","name":"signature","type":"bytes"}],"internalType":"struct BasicOrderParameters","name":"parameters","type":"tuple"}],"name":"fulfillBasicOrder","outputs":[{"internalType":"bool","name":"fulfilled","type":"bool"}],"stateMutability":"payable","type":"function"},{"inputs":[{"components":[{"components":[{"internalType":"address","name":"offerer","type":"address"},{"internalType":"address","name":"zone","type":"address"},{"components":[{"internalType":"enum ItemType","name":"itemType","type":"uint8"},{"internalType":"address","name":"token","type":"address"},{"internalType":"uint256","name":"identifierOrCriteria","type":"uint256"},{"internalType":"uint256","name":"startAmount","type":"uint256"},{"internalType":"uint256","name":"endAmount","type":"uint256"}],"internalType":"struct OfferItem[]","name":"offer","type":"tuple[]"},{"components":[{"internalType":"enum ItemType","name":"itemType","type":"uint8"},{"internalType":"address","name":"token","type":"address"},{"internalType":"uint256","name":"identifierOrCriteria","type":"uint256"},{"internalType":"uint256","name":"startAmount","type":"uint256"},{"internalType":"uint256","name":"endAmount","type":"uint256"},{"internalType":"address payable","name":"recipient","type":"address"}],"internalType":"struct ConsiderationItem[]","name":"consideration","type":"tuple[]"},{"internalType":"enum OrderType","name":"orderType","type":"uint8"},{"internalType":"uint256","name":"startTime","type":"uint256"},{"internalType":"uint256","name":"endTime","type":"uint256"},{"internalType":"bytes32","name":"zoneHash","type":"bytes32"},{"internalType":"uint256","name":"salt","type":"uint256"},{"internalType":"bytes32","name":"conduitKey","type":"bytes32"},{"internalType":"uint256","name":"totalOriginalConsiderationItems","type":"uint256"}],"internalType":"struct OrderParameters","name":"parameters","type":"tuple"},{"internalType":"bytes","name":"signature","type":"bytes"}],"internalType":"struct Order","name":"order","type":"tuple"},{"internalType":"bytes32","name":"fulfillerConduitKey","type":"bytes32"}],"name":"fulfillOrder","outputs":[{"internalType":"bool","name":"fulfilled","type":"bool"}],"stateMutability":"payable","type":"function"},{"inputs":[{"internalType":"address","name":"offerer","type":"address"}],"name":"getCounter","outputs":[{"internalType":"uint256","name":"counter","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"components":[{"internalType":"address","name":"offerer","type":"address"},{"internalType":"address","name":"zone","type":"address"},{"components":[{"internalType":"enum ItemType","name":"itemType","type":"uint8"},{"internalType":"address","name":"token","type":"address"},{"internalType":"uint256","name":"identifierOrCriteria","type":"uint256"},{"internalType":"uint256","name":"startAmount","type":"uint256"},{"internalType":"uint256","name":"endAmount","type":"uint256"}],"internalType":"struct OfferItem[]","name":"offer","type":"tuple[]"},{"components":[{"internalType":"enum ItemType","name":"itemType","type":"uint8"},{"internalType":"address","name":"token","type":"address"},{"internalType":"uint256","name":"identifierOrCriteria","type":"uint256"},{"internalType":"uint256","name":"startAmount","type":"uint256"},{"internalType":"uint256","name":"endAmount","type":"uint256"},{"internalType":"address payable","name":"recipient","type":"address"}],"internalType":"struct ConsiderationItem[]","name":"consideration","type":"tuple[]"},{"internalType":"enum OrderType","name":"orderType","type":"uint8"},{"internalType":"uint256","name":"startTime","type":"uint256"},{"internalType":"uint256","name":"endTime","type":"uint256"},{"internalType":"bytes32","name":"zoneHash","type":"bytes32"},{"internalType":"uint256","name":"salt","type":"uint256"},{"internalType":"bytes32","name":"conduitKey","type":"bytes32"},{"internalType":"uint256","name":"counter","type":"uint256"}],"internalType":"struct OrderComponents","name":"order","type":"tuple"}],"name":"getOrderHash","outputs":[{"internalType":"bytes32","name":"orderHash","type":"bytes32"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"bytes32","name":"orderHash","type":"bytes32"}],"name":"getOrderStatus","outputs":[{"internalType":"bool","name":"isValidated","type":"bool"},{"internalType":"bool","name":"isCancelled","type":"bool"},{"internalType":"uint256","name":"totalFilled","type":"uint256"},{"internalType":"uint256","name":"totalSize","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"incrementCounter","outputs":[{"internalType":"uint256","name":"newCounter","type":"uint256"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[],"name":"information","outputs":[{"internalType":"string","name":"version","type":"string"},{"internalType":"bytes32","name":"domainSeparator","type":"bytes32"},{"internalType":"address","name":"conduitController","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[{"components":[{"components":[{"internalType":"address","name":"offerer","type":"address"},{"internalType":"address","name":"zone","type":"address"},{"components":[{"internalType":"enum ItemType","name":"itemType","type":"uint8"},{"internalType":"address","name":"token","type":"address"},{"internalType":"uint256","name":"identifierOrCriteria","type":"uint256"},{"internalType":"uint256","name":"startAmount","type":"uint256"},{"internalType":"uint256","name":"endAmount","type":"uint256"}],"internalType":"struct OfferItem[]","name":"offer","type":"tuple[]"},{"components":[{"internalType":"enum ItemType","name":"itemType","type":"uint8"},{"internalType":"address","name":"token","type":"address"},{"internalType":"uint256","name":"identifierOrCriteria","type":"uint256"},{"internalType":"uint256","name":"startAmount","type":"uint256"},{"internalType":"uint256","name":"endAmount","type":"uint256"},{"internalType":"address payable","name":"recipient","type":"address"}],"internalType":"struct ConsiderationItem[]","name":"consideration","type":"tuple[]"},{"internalType":"enum OrderType","name":"orderType","type":"uint8"},{"internalType":"uint256","name":"startTime","type":"uint256"},{"internalType":"uint256","name":"endTime","type":"uint256"},{"internalType":"bytes32","name":"zoneHash","type":"bytes32"},{"internalType":"uint256","name":"salt","type":"uint256"},{"internalType":"bytes32","name":"conduitKey","type":"bytes32"},{"internalType":"uint256","name":"totalOriginalConsiderationItems","type":"uint256"}],"internalType":"struct OrderParameters","name":"parameters","type":"tuple"},{"internalType":"uint120","name":"numerator","type":"uint120"},{"internalType":"uint120","name":"denominator","type":"uint120"},{"internalType":"bytes","name":"signature","type":"bytes"},{"internalType":"bytes","name":"extraData","type":"bytes"}],"internalType":"struct AdvancedOrder[]","name":"advancedOrders","type":"tuple[]"},{"components":[{"internalType":"uint256","name":"orderIndex","type":"uint256"},{"internalType":"enum Side","name":"side","type":"uint8"},{"internalType":"uint256","name":"index","type":"uint256"},{"internalType":"uint256","name":"identifier","type":"uint256"},{"internalType":"bytes32[]","name":"criteriaProof","type":"bytes32[]"}],"internalType":"struct CriteriaResolver[]","name":"criteriaResolvers","type":"tuple[]"},{"components":[{"components":[{"internalType":"uint256","name":"orderIndex","type":"uint256"},{"internalType":"uint256","name":"itemIndex","type":"uint256"}],"internalType":"struct FulfillmentComponent[]","name":"offerComponents","type":"tuple[]"},{"components":[{"internalType":"uint256","name":"orderIndex","type":"uint256"},{"internalType":"uint256","name":"itemIndex","type":"uint256"}],"internalType":"struct FulfillmentComponent[]","name":"considerationComponents","type":"tuple[]"}],"internalType":"struct Fulfillment[]","name":"fulfillments","type":"tuple[]"}],"name":"matchAdvancedOrders","outputs":[{"components":[{"components":[{"internalType":"enum ItemType","name":"itemType","type":"uint8"},{"internalType":"address","name":"token","type":"address"},{"internalType":"uint256","name":"identifier","type":"uint256"},{"internalType":"uint256","name":"amount","type":"uint256"},{"internalType":"address payable","name":"recipient","type":"address"}],"internalType":"struct ReceivedItem","name":"item","type":"tuple"},{"internalType":"address","name":"offerer","type":"address"},{"internalType":"bytes32","name":"conduitKey","type":"bytes32"}],"internalType":"struct Execution[]","name":"executions","type":"tuple[]"}],"stateMutability":"payable","type":"function"},{"inputs":[{"components":[{"components":[{"internalType":"address","name":"offerer","type":"address"},{"internalType":"address","name":"zone","type":"address"},{"components":[{"internalType":"enum ItemType","name":"itemType","type":"uint8"},{"internalType":"address","name":"token","type":"address"},{"internalType":"uint256","name":"identifierOrCriteria","type":"uint256"},{"internalType":"uint256","name":"startAmount","type":"uint256"},{"internalType":"uint256","name":"endAmount","type":"uint256"}],"internalType":"struct OfferItem[]","name":"offer","type":"tuple[]"},{"components":[{"internalType":"enum ItemType","name":"itemType","type":"uint8"},{"internalType":"address","name":"token","type":"address"},{"internalType":"uint256","name":"identifierOrCriteria","type":"uint256"},{"internalType":"uint256","name":"startAmount","type":"uint256"},{"internalType":"uint256","name":"endAmount","type":"uint256"},{"internalType":"address payable","name":"recipient","type":"address"}],"internalType":"struct ConsiderationItem[]","name":"consideration","type":"tuple[]"},{"internalType":"enum OrderType","name":"orderType","type":"uint8"},{"internalType":"uint256","name":"startTime","type":"uint256"},{"internalType":"uint256","name":"endTime","type":"uint256"},{"internalType":"bytes32","name":"zoneHash","type":"bytes32"},{"internalType":"uint256","name":"salt","type":"uint256"},{"internalType":"bytes32","name":"conduitKey","type":"bytes32"},{"internalType":"uint256","name":"totalOriginalConsiderationItems","type":"uint256"}],"internalType":"struct OrderParameters","name":"parameters","type":"tuple"},{"internalType":"bytes","name":"signature","type":"bytes"}],"internalType":"struct Order[]","name":"orders","type":"tuple[]"},{"components":[{"components":[{"internalType":"uint256","name":"orderIndex","type":"uint256"},{"internalType":"uint256","name":"itemIndex","type":"uint256"}],"internalType":"struct FulfillmentComponent[]","name":"offerComponents","type":"tuple[]"},{"components":[{"internalType":"uint256","name":"orderIndex","type":"uint256"},{"internalType":"uint256","name":"itemIndex","type":"uint256"}],"internalType":"struct FulfillmentComponent[]","name":"considerationComponents","type":"tuple[]"}],"internalType":"struct Fulfillment[]","name":"fulfillments","type":"tuple[]"}],"name":"matchOrders","outputs":[{"components":[{"components":[{"internalType":"enum ItemType","name":"itemType","type":"uint8"},{"internalType":"address","name":"token","type":"address"},{"internalType":"uint256","name":"identifier","type":"uint256"},{"internalType":"uint256","name":"amount","type":"uint256"},{"internalType":"address payable","name":"recipient","type":"address"}],"internalType":"struct ReceivedItem","name":"item","type":"tuple"},{"internalType":"address","name":"offerer","type":"address"},{"internalType":"bytes32","name":"conduitKey","type":"bytes32"}],"internalType":"struct Execution[]","name":"executions","type":"tuple[]"}],"stateMutability":"payable","type":"function"},{"inputs":[],"name":"name","outputs":[{"internalType":"string","name":"contractName","type":"string"}],"stateMutability":"pure","type":"function"},{"inputs":[{"components":[{"components":[{"internalType":"address","name":"offerer","type":"address"},{"internalType":"address","name":"zone","type":"address"},{"components":[{"internalType":"enum ItemType","name":"itemType","type":"uint8"},{"internalType":"address","name":"token","type":"address"},{"internalType":"uint256","name":"identifierOrCriteria","type":"uint256"},{"internalType":"uint256","name":"startAmount","type":"uint256"},{"internalType":"uint256","name":"endAmount","type":"uint256"}],"internalType":"struct OfferItem[]","name":"offer","type":"tuple[]"},{"components":[{"internalType":"enum ItemType","name":"itemType","type":"uint8"},{"internalType":"address","name":"token","type":"address"},{"internalType":"uint256","name":"identifierOrCriteria","type":"uint256"},{"internalType":"uint256","name":"startAmount","type":"uint256"},{"internalType":"uint256","name":"endAmount","type":"uint256"},{"internalType":"address payable","name":"recipient","type":"address"}],"internalType":"struct ConsiderationItem[]","name":"consideration","type":"tuple[]"},{"internalType":"enum OrderType","name":"orderType","type":"uint8"},{"internalType":"uint256","name":"startTime","type":"uint256"},{"internalType":"uint256","name":"endTime","type":"uint256"},{"internalType":"bytes32","name":"zoneHash","type":"bytes32"},{"internalType":"uint256","name":"salt","type":"uint256"},{"internalType":"bytes32","name":"conduitKey","type":"bytes32"},{"internalType":"uint256","name":"totalOriginalConsiderationItems","type":"uint256"}],"internalType":"struct OrderParameters","name":"parameters","type":"tuple"},{"internalType":"bytes","name":"signature","type":"bytes"}],"internalType":"struct Order[]","name":"orders","type":"tuple[]"}],"name":"validate","outputs":[{"internalType":"bool","name":"validated","type":"bool"}],"stateMutability":"nonpayable","type":"function"}]
    self.contract = w3.eth.contract(address="0x00000000006c3852cbEf3e08E8dF289169EdE581", abi=self.abi)
    self.poll_filter = self.contract.events.OrderFulfilled.createFilter(fromBlock="latest")

    self.db = db
    with db.begin() as txn:
      self.block = json.loads(txn.get(b"seaport_block"))

    self.start_block = w3.eth.block_number
    self.i = 0
    self.step = 10_000
    self.crawl_finished = False

  def extract_addresses(self, entries):
    addresses = []

    for entry in entries:
      args = entry["args"]

      for item in args["offer"]:
        address = item[1]
        if address not in addresses and address != web3.constants.ADDRESS_ZERO:
          addresses.append(address)

      for item in args["consideration"]:
        address = item[1]
        if address not in addresses and address != web3.constants.ADDRESS_ZERO:
          addresses.append(address)

    return addresses

  async def find_addresses(self):
    if self.crawl_finished:
      entries = []
    else:
      fromBlock = self.block + self.i * self.step
      toBlock = self.block + (self.i + 1) * self.step
      if toBlock > self.start_block:
        toBlock = self.start_block

      with self.db.begin(write=True) as txn:
        txn.put(b"seaport_block", json.dumps(fromBlock).encode())

      try:
        crawl_filter = self.contract.events.OrderFulfilled.createFilter(fromBlock=fromBlock, toBlock=toBlock)
        entries = crawl_filter.get_all_entries()
      except ValueError as e:
        if "message" in e.args[0] and e.args[0]["message"] == "query returned more than 10000 results":
          self.step = self.step * 4 // 5
          return await self.find_addresses()
        else:
          raise e

      if toBlock == self.start_block:
        self.crawl_finished = True

      self.i += 1

    entries.extend(self.poll_filter.get_new_entries())

    return self.extract_addresses(entries)

  async def sleep(self):
    if self.crawl_finished:
      await asyncio.sleep(10)
    else:
      await asyncio.sleep(1)


class LooksRare:
  def __init__(self, w3, db):
    self.abi = [{"inputs":[{"internalType":"address","name":"_currencyManager","type":"address"},{"internalType":"address","name":"_executionManager","type":"address"},{"internalType":"address","name":"_royaltyFeeManager","type":"address"},{"internalType":"address","name":"_WETH","type":"address"},{"internalType":"address","name":"_protocolFeeRecipient","type":"address"}],"stateMutability":"nonpayable","type":"constructor"},{"anonymous":False,"inputs":[{"indexed":True,"internalType":"address","name":"user","type":"address"},{"indexed":False,"internalType":"uint256","name":"newMinNonce","type":"uint256"}],"name":"CancelAllOrders","type":"event"},{"anonymous":False,"inputs":[{"indexed":True,"internalType":"address","name":"user","type":"address"},{"indexed":False,"internalType":"uint256[]","name":"orderNonces","type":"uint256[]"}],"name":"CancelMultipleOrders","type":"event"},{"anonymous":False,"inputs":[{"indexed":True,"internalType":"address","name":"currencyManager","type":"address"}],"name":"NewCurrencyManager","type":"event"},{"anonymous":False,"inputs":[{"indexed":True,"internalType":"address","name":"executionManager","type":"address"}],"name":"NewExecutionManager","type":"event"},{"anonymous":False,"inputs":[{"indexed":True,"internalType":"address","name":"protocolFeeRecipient","type":"address"}],"name":"NewProtocolFeeRecipient","type":"event"},{"anonymous":False,"inputs":[{"indexed":True,"internalType":"address","name":"royaltyFeeManager","type":"address"}],"name":"NewRoyaltyFeeManager","type":"event"},{"anonymous":False,"inputs":[{"indexed":True,"internalType":"address","name":"transferSelectorNFT","type":"address"}],"name":"NewTransferSelectorNFT","type":"event"},{"anonymous":False,"inputs":[{"indexed":True,"internalType":"address","name":"previousOwner","type":"address"},{"indexed":True,"internalType":"address","name":"newOwner","type":"address"}],"name":"OwnershipTransferred","type":"event"},{"anonymous":False,"inputs":[{"indexed":True,"internalType":"address","name":"collection","type":"address"},{"indexed":True,"internalType":"uint256","name":"tokenId","type":"uint256"},{"indexed":True,"internalType":"address","name":"royaltyRecipient","type":"address"},{"indexed":False,"internalType":"address","name":"currency","type":"address"},{"indexed":False,"internalType":"uint256","name":"amount","type":"uint256"}],"name":"RoyaltyPayment","type":"event"},{"anonymous":False,"inputs":[{"indexed":False,"internalType":"bytes32","name":"orderHash","type":"bytes32"},{"indexed":False,"internalType":"uint256","name":"orderNonce","type":"uint256"},{"indexed":True,"internalType":"address","name":"taker","type":"address"},{"indexed":True,"internalType":"address","name":"maker","type":"address"},{"indexed":True,"internalType":"address","name":"strategy","type":"address"},{"indexed":False,"internalType":"address","name":"currency","type":"address"},{"indexed":False,"internalType":"address","name":"collection","type":"address"},{"indexed":False,"internalType":"uint256","name":"tokenId","type":"uint256"},{"indexed":False,"internalType":"uint256","name":"amount","type":"uint256"},{"indexed":False,"internalType":"uint256","name":"price","type":"uint256"}],"name":"TakerAsk","type":"event"},{"anonymous":False,"inputs":[{"indexed":False,"internalType":"bytes32","name":"orderHash","type":"bytes32"},{"indexed":False,"internalType":"uint256","name":"orderNonce","type":"uint256"},{"indexed":True,"internalType":"address","name":"taker","type":"address"},{"indexed":True,"internalType":"address","name":"maker","type":"address"},{"indexed":True,"internalType":"address","name":"strategy","type":"address"},{"indexed":False,"internalType":"address","name":"currency","type":"address"},{"indexed":False,"internalType":"address","name":"collection","type":"address"},{"indexed":False,"internalType":"uint256","name":"tokenId","type":"uint256"},{"indexed":False,"internalType":"uint256","name":"amount","type":"uint256"},{"indexed":False,"internalType":"uint256","name":"price","type":"uint256"}],"name":"TakerBid","type":"event"},{"inputs":[],"name":"DOMAIN_SEPARATOR","outputs":[{"internalType":"bytes32","name":"","type":"bytes32"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"WETH","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint256","name":"minNonce","type":"uint256"}],"name":"cancelAllOrdersForSender","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256[]","name":"orderNonces","type":"uint256[]"}],"name":"cancelMultipleMakerOrders","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[],"name":"currencyManager","outputs":[{"internalType":"contract ICurrencyManager","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"executionManager","outputs":[{"internalType":"contract IExecutionManager","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"user","type":"address"},{"internalType":"uint256","name":"orderNonce","type":"uint256"}],"name":"isUserOrderNonceExecutedOrCancelled","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"view","type":"function"},{"inputs":[{"components":[{"internalType":"bool","name":"isOrderAsk","type":"bool"},{"internalType":"address","name":"taker","type":"address"},{"internalType":"uint256","name":"price","type":"uint256"},{"internalType":"uint256","name":"tokenId","type":"uint256"},{"internalType":"uint256","name":"minPercentageToAsk","type":"uint256"},{"internalType":"bytes","name":"params","type":"bytes"}],"internalType":"struct OrderTypes.TakerOrder","name":"takerBid","type":"tuple"},{"components":[{"internalType":"bool","name":"isOrderAsk","type":"bool"},{"internalType":"address","name":"signer","type":"address"},{"internalType":"address","name":"collection","type":"address"},{"internalType":"uint256","name":"price","type":"uint256"},{"internalType":"uint256","name":"tokenId","type":"uint256"},{"internalType":"uint256","name":"amount","type":"uint256"},{"internalType":"address","name":"strategy","type":"address"},{"internalType":"address","name":"currency","type":"address"},{"internalType":"uint256","name":"nonce","type":"uint256"},{"internalType":"uint256","name":"startTime","type":"uint256"},{"internalType":"uint256","name":"endTime","type":"uint256"},{"internalType":"uint256","name":"minPercentageToAsk","type":"uint256"},{"internalType":"bytes","name":"params","type":"bytes"},{"internalType":"uint8","name":"v","type":"uint8"},{"internalType":"bytes32","name":"r","type":"bytes32"},{"internalType":"bytes32","name":"s","type":"bytes32"}],"internalType":"struct OrderTypes.MakerOrder","name":"makerAsk","type":"tuple"}],"name":"matchAskWithTakerBid","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"components":[{"internalType":"bool","name":"isOrderAsk","type":"bool"},{"internalType":"address","name":"taker","type":"address"},{"internalType":"uint256","name":"price","type":"uint256"},{"internalType":"uint256","name":"tokenId","type":"uint256"},{"internalType":"uint256","name":"minPercentageToAsk","type":"uint256"},{"internalType":"bytes","name":"params","type":"bytes"}],"internalType":"struct OrderTypes.TakerOrder","name":"takerBid","type":"tuple"},{"components":[{"internalType":"bool","name":"isOrderAsk","type":"bool"},{"internalType":"address","name":"signer","type":"address"},{"internalType":"address","name":"collection","type":"address"},{"internalType":"uint256","name":"price","type":"uint256"},{"internalType":"uint256","name":"tokenId","type":"uint256"},{"internalType":"uint256","name":"amount","type":"uint256"},{"internalType":"address","name":"strategy","type":"address"},{"internalType":"address","name":"currency","type":"address"},{"internalType":"uint256","name":"nonce","type":"uint256"},{"internalType":"uint256","name":"startTime","type":"uint256"},{"internalType":"uint256","name":"endTime","type":"uint256"},{"internalType":"uint256","name":"minPercentageToAsk","type":"uint256"},{"internalType":"bytes","name":"params","type":"bytes"},{"internalType":"uint8","name":"v","type":"uint8"},{"internalType":"bytes32","name":"r","type":"bytes32"},{"internalType":"bytes32","name":"s","type":"bytes32"}],"internalType":"struct OrderTypes.MakerOrder","name":"makerAsk","type":"tuple"}],"name":"matchAskWithTakerBidUsingETHAndWETH","outputs":[],"stateMutability":"payable","type":"function"},{"inputs":[{"components":[{"internalType":"bool","name":"isOrderAsk","type":"bool"},{"internalType":"address","name":"taker","type":"address"},{"internalType":"uint256","name":"price","type":"uint256"},{"internalType":"uint256","name":"tokenId","type":"uint256"},{"internalType":"uint256","name":"minPercentageToAsk","type":"uint256"},{"internalType":"bytes","name":"params","type":"bytes"}],"internalType":"struct OrderTypes.TakerOrder","name":"takerAsk","type":"tuple"},{"components":[{"internalType":"bool","name":"isOrderAsk","type":"bool"},{"internalType":"address","name":"signer","type":"address"},{"internalType":"address","name":"collection","type":"address"},{"internalType":"uint256","name":"price","type":"uint256"},{"internalType":"uint256","name":"tokenId","type":"uint256"},{"internalType":"uint256","name":"amount","type":"uint256"},{"internalType":"address","name":"strategy","type":"address"},{"internalType":"address","name":"currency","type":"address"},{"internalType":"uint256","name":"nonce","type":"uint256"},{"internalType":"uint256","name":"startTime","type":"uint256"},{"internalType":"uint256","name":"endTime","type":"uint256"},{"internalType":"uint256","name":"minPercentageToAsk","type":"uint256"},{"internalType":"bytes","name":"params","type":"bytes"},{"internalType":"uint8","name":"v","type":"uint8"},{"internalType":"bytes32","name":"r","type":"bytes32"},{"internalType":"bytes32","name":"s","type":"bytes32"}],"internalType":"struct OrderTypes.MakerOrder","name":"makerBid","type":"tuple"}],"name":"matchBidWithTakerAsk","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[],"name":"owner","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"protocolFeeRecipient","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"renounceOwnership","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[],"name":"royaltyFeeManager","outputs":[{"internalType":"contract IRoyaltyFeeManager","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"newOwner","type":"address"}],"name":"transferOwnership","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[],"name":"transferSelectorNFT","outputs":[{"internalType":"contract ITransferSelectorNFT","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"_currencyManager","type":"address"}],"name":"updateCurrencyManager","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"_executionManager","type":"address"}],"name":"updateExecutionManager","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"_protocolFeeRecipient","type":"address"}],"name":"updateProtocolFeeRecipient","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"_royaltyFeeManager","type":"address"}],"name":"updateRoyaltyFeeManager","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"_transferSelectorNFT","type":"address"}],"name":"updateTransferSelectorNFT","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"","type":"address"}],"name":"userMinOrderNonce","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"}]
    self.contract = w3.eth.contract(address="0x59728544B08AB483533076417FbBB2fD0B17CE3a", abi=self.abi)
    self.ask_poll_filter = self.contract.events.TakerAsk.createFilter(fromBlock="latest")
    self.bid_poll_filter = self.contract.events.TakerBid.createFilter(fromBlock="latest")
    
    self.db = db
    with db.begin() as txn:
      self.block = json.loads(txn.get(b"looksrare_block"))

    self.start_block = w3.eth.block_number
    self.i = 0
    self.step = 10_000
    self.crawl_finished = False

  def extract_addresses(self, entries):
    addresses = []

    for entry in entries:
      args = entry["args"]

      address = args["collection"]
      if address not in addresses and address != web3.constants.ADDRESS_ZERO:
        addresses.append(address)

    return addresses

  async def find_addresses(self):
    if self.crawl_finished:
      entries = []
    else:
      fromBlock = self.block + self.i * self.step
      toBlock = self.block + (self.i + 1) * self.step
      if toBlock > self.start_block:
        toBlock = self.start_block

      with self.db.begin(write=True) as txn:
        txn.put(b"looksrare_block", json.dumps(fromBlock).encode())

      try:
        ask_crawl_filter = self.contract.events.TakerAsk.createFilter(fromBlock=fromBlock, toBlock=toBlock)
        bid_crawl_filter = self.contract.events.TakerBid.createFilter(fromBlock=fromBlock, toBlock=toBlock)

        async def get_ask_entries(): return ask_crawl_filter.get_all_entries()
        async def get_bid_entries(): return bid_crawl_filter.get_all_entries()

        [ask_entries, bid_entries] = await asyncio.gather(
          asyncio.create_task(get_ask_entries()),
          asyncio.create_task(get_bid_entries()),
        )
        entries = ask_entries + bid_entries
      except ValueError as e:
        if "message" in e.args[0] and e.args[0]["message"] == "query returned more than 10000 results":
          self.step = self.step * 4 // 5
          return await self.find_addresses()
        else:
          raise e

      if toBlock == self.start_block:
        self.crawl_finished = True

      self.i += 1

    async def get_ask_entries(): return self.ask_poll_filter.get_new_entries()
    async def get_bid_entries(): return self.bid_poll_filter.get_new_entries()

    [ask_entries, bid_entries] = await asyncio.gather(
      asyncio.create_task(get_ask_entries()),
      asyncio.create_task(get_bid_entries()),
    )
    entries.extend(ask_entries)
    entries.extend(bid_entries)

    return self.extract_addresses(entries)

  async def sleep(self):
    if self.crawl_finished:
      await asyncio.sleep(10)
    else:
      await asyncio.sleep(1)


class Rarible:
  def __init__(self, w3, db):
    self.abi = [{"anonymous":False,"inputs":[{"indexed":False,"internalType":"bytes32","name":"hash","type":"bytes32"}],"name":"Cancel","type":"event"},{"anonymous":False,"inputs":[{"indexed":False,"internalType":"bytes32","name":"leftHash","type":"bytes32"},{"indexed":False,"internalType":"bytes32","name":"rightHash","type":"bytes32"},{"indexed":False,"internalType":"uint256","name":"newLeftFill","type":"uint256"},{"indexed":False,"internalType":"uint256","name":"newRightFill","type":"uint256"}],"name":"Match","type":"event"},{"anonymous":False,"inputs":[{"indexed":True,"internalType":"bytes4","name":"assetType","type":"bytes4"},{"indexed":False,"internalType":"address","name":"matcher","type":"address"}],"name":"MatcherChange","type":"event"},{"anonymous":False,"inputs":[{"indexed":True,"internalType":"address","name":"previousOwner","type":"address"},{"indexed":True,"internalType":"address","name":"newOwner","type":"address"}],"name":"OwnershipTransferred","type":"event"},{"anonymous":False,"inputs":[{"indexed":True,"internalType":"bytes4","name":"assetType","type":"bytes4"},{"indexed":False,"internalType":"address","name":"proxy","type":"address"}],"name":"ProxyChange","type":"event"},{"inputs":[{"internalType":"address","name":"_transferProxy","type":"address"},{"internalType":"address","name":"_erc20TransferProxy","type":"address"},{"internalType":"uint256","name":"newProtocolFee","type":"uint256"},{"internalType":"address","name":"newDefaultFeeReceiver","type":"address"},{"internalType":"contract IRoyaltiesProvider","name":"newRoyaltiesProvider","type":"address"}],"name":"__ExchangeV2_init","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"components":[{"internalType":"address","name":"maker","type":"address"},{"components":[{"components":[{"internalType":"bytes4","name":"assetClass","type":"bytes4"},{"internalType":"bytes","name":"data","type":"bytes"}],"internalType":"struct LibAsset.AssetType","name":"assetType","type":"tuple"},{"internalType":"uint256","name":"value","type":"uint256"}],"internalType":"struct LibAsset.Asset","name":"makeAsset","type":"tuple"},{"internalType":"address","name":"taker","type":"address"},{"components":[{"components":[{"internalType":"bytes4","name":"assetClass","type":"bytes4"},{"internalType":"bytes","name":"data","type":"bytes"}],"internalType":"struct LibAsset.AssetType","name":"assetType","type":"tuple"},{"internalType":"uint256","name":"value","type":"uint256"}],"internalType":"struct LibAsset.Asset","name":"takeAsset","type":"tuple"},{"internalType":"uint256","name":"salt","type":"uint256"},{"internalType":"uint256","name":"start","type":"uint256"},{"internalType":"uint256","name":"end","type":"uint256"},{"internalType":"bytes4","name":"dataType","type":"bytes4"},{"internalType":"bytes","name":"data","type":"bytes"}],"internalType":"struct LibOrder.Order","name":"order","type":"tuple"}],"name":"cancel","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"components":[{"internalType":"address","name":"bidMaker","type":"address"},{"internalType":"uint256","name":"bidNftAmount","type":"uint256"},{"internalType":"bytes4","name":"nftAssetClass","type":"bytes4"},{"internalType":"bytes","name":"nftData","type":"bytes"},{"internalType":"uint256","name":"bidPaymentAmount","type":"uint256"},{"internalType":"address","name":"paymentToken","type":"address"},{"internalType":"uint256","name":"bidSalt","type":"uint256"},{"internalType":"uint256","name":"bidStart","type":"uint256"},{"internalType":"uint256","name":"bidEnd","type":"uint256"},{"internalType":"bytes4","name":"bidDataType","type":"bytes4"},{"internalType":"bytes","name":"bidData","type":"bytes"},{"internalType":"bytes","name":"bidSignature","type":"bytes"},{"internalType":"uint256","name":"sellOrderPaymentAmount","type":"uint256"},{"internalType":"uint256","name":"sellOrderNftAmount","type":"uint256"},{"internalType":"bytes","name":"sellOrderData","type":"bytes"}],"internalType":"struct LibDirectTransfer.AcceptBid","name":"direct","type":"tuple"}],"name":"directAcceptBid","outputs":[],"stateMutability":"payable","type":"function"},{"inputs":[{"components":[{"internalType":"address","name":"sellOrderMaker","type":"address"},{"internalType":"uint256","name":"sellOrderNftAmount","type":"uint256"},{"internalType":"bytes4","name":"nftAssetClass","type":"bytes4"},{"internalType":"bytes","name":"nftData","type":"bytes"},{"internalType":"uint256","name":"sellOrderPaymentAmount","type":"uint256"},{"internalType":"address","name":"paymentToken","type":"address"},{"internalType":"uint256","name":"sellOrderSalt","type":"uint256"},{"internalType":"uint256","name":"sellOrderStart","type":"uint256"},{"internalType":"uint256","name":"sellOrderEnd","type":"uint256"},{"internalType":"bytes4","name":"sellOrderDataType","type":"bytes4"},{"internalType":"bytes","name":"sellOrderData","type":"bytes"},{"internalType":"bytes","name":"sellOrderSignature","type":"bytes"},{"internalType":"uint256","name":"buyOrderPaymentAmount","type":"uint256"},{"internalType":"uint256","name":"buyOrderNftAmount","type":"uint256"},{"internalType":"bytes","name":"buyOrderData","type":"bytes"}],"internalType":"struct LibDirectTransfer.Purchase","name":"direct","type":"tuple"}],"name":"directPurchase","outputs":[],"stateMutability":"payable","type":"function"},{"inputs":[{"internalType":"bytes32","name":"","type":"bytes32"}],"name":"fills","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"components":[{"internalType":"address","name":"maker","type":"address"},{"components":[{"components":[{"internalType":"bytes4","name":"assetClass","type":"bytes4"},{"internalType":"bytes","name":"data","type":"bytes"}],"internalType":"struct LibAsset.AssetType","name":"assetType","type":"tuple"},{"internalType":"uint256","name":"value","type":"uint256"}],"internalType":"struct LibAsset.Asset","name":"makeAsset","type":"tuple"},{"internalType":"address","name":"taker","type":"address"},{"components":[{"components":[{"internalType":"bytes4","name":"assetClass","type":"bytes4"},{"internalType":"bytes","name":"data","type":"bytes"}],"internalType":"struct LibAsset.AssetType","name":"assetType","type":"tuple"},{"internalType":"uint256","name":"value","type":"uint256"}],"internalType":"struct LibAsset.Asset","name":"takeAsset","type":"tuple"},{"internalType":"uint256","name":"salt","type":"uint256"},{"internalType":"uint256","name":"start","type":"uint256"},{"internalType":"uint256","name":"end","type":"uint256"},{"internalType":"bytes4","name":"dataType","type":"bytes4"},{"internalType":"bytes","name":"data","type":"bytes"}],"internalType":"struct LibOrder.Order","name":"orderLeft","type":"tuple"},{"internalType":"bytes","name":"signatureLeft","type":"bytes"},{"components":[{"internalType":"address","name":"maker","type":"address"},{"components":[{"components":[{"internalType":"bytes4","name":"assetClass","type":"bytes4"},{"internalType":"bytes","name":"data","type":"bytes"}],"internalType":"struct LibAsset.AssetType","name":"assetType","type":"tuple"},{"internalType":"uint256","name":"value","type":"uint256"}],"internalType":"struct LibAsset.Asset","name":"makeAsset","type":"tuple"},{"internalType":"address","name":"taker","type":"address"},{"components":[{"components":[{"internalType":"bytes4","name":"assetClass","type":"bytes4"},{"internalType":"bytes","name":"data","type":"bytes"}],"internalType":"struct LibAsset.AssetType","name":"assetType","type":"tuple"},{"internalType":"uint256","name":"value","type":"uint256"}],"internalType":"struct LibAsset.Asset","name":"takeAsset","type":"tuple"},{"internalType":"uint256","name":"salt","type":"uint256"},{"internalType":"uint256","name":"start","type":"uint256"},{"internalType":"uint256","name":"end","type":"uint256"},{"internalType":"bytes4","name":"dataType","type":"bytes4"},{"internalType":"bytes","name":"data","type":"bytes"}],"internalType":"struct LibOrder.Order","name":"orderRight","type":"tuple"},{"internalType":"bytes","name":"signatureRight","type":"bytes"}],"name":"matchOrders","outputs":[],"stateMutability":"payable","type":"function"},{"inputs":[],"name":"owner","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"renounceOwnership","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[],"name":"royaltiesRegistry","outputs":[{"internalType":"contract IRoyaltiesProvider","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"bytes4","name":"assetType","type":"bytes4"},{"internalType":"address","name":"matcher","type":"address"}],"name":"setAssetMatcher","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"contract IRoyaltiesProvider","name":"newRoyaltiesRegistry","type":"address"}],"name":"setRoyaltiesRegistry","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"bytes4","name":"assetType","type":"bytes4"},{"internalType":"address","name":"proxy","type":"address"}],"name":"setTransferProxy","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"newOwner","type":"address"}],"name":"transferOwnership","outputs":[],"stateMutability":"nonpayable","type":"function"}]
    self.contract = w3.eth.contract(address="0x9757F2d2b135150BBeb65308D4a91804107cd8D6", abi=self.abi)
    self.poll_filter = self.contract.events.Match.createFilter(fromBlock="latest")
    
    self.db = db
    with db.begin() as txn:
      self.block = json.loads(txn.get(b"rarible_block"))

    self.start_block = w3.eth.block_number
    self.i = 0
    self.step = 10_000
    self.crawl_finished = False

  def extract_addresses(self, entries):
    return entries

  async def find_addresses(self):
    if self.crawl_finished:
      entries = []
    else:
      fromBlock = self.block + self.i * self.step
      toBlock = self.block + (self.i + 1) * self.step
      if toBlock > self.start_block:
        toBlock = self.start_block

      # with self.db.begin(write=True) as txn:
      #   txn.put(b"rarible_block", json.dumps(fromBlock).encode())

      # try:
      crawl_filter = self.contract.events.Match.createFilter(fromBlock=fromBlock, toBlock=toBlock)
      entries = crawl_filter.get_all_entries()
      # except ValueError as e:
      #   if "message" in e.args[0] and e.args[0]["message"] == "query returned more than 10000 results":
      #     self.step = self.step * 4 // 5
      #     return await self.find_addresses()
      #   else:
      #     raise e

      if toBlock == self.start_block:
        self.crawl_finished = True

      self.i += 1

    entries.extend(self.poll_filter.get_new_entries())

    return self.extract_addresses(entries)

  async def sleep(self):
    if self.crawl_finished:
      await asyncio.sleep(10)
    else:
      await asyncio.sleep(1)


class Foundation:
  def __init__(self, w3, db):
    self.abi = [{"inputs":[{"internalType":"address payable","name":"treasury","type":"address"},{"internalType":"address","name":"feth","type":"address"},{"internalType":"address","name":"royaltyRegistry","type":"address"},{"internalType":"uint256","name":"duration","type":"uint256"}],"stateMutability":"nonpayable","type":"constructor"},{"inputs":[],"name":"FoundationTreasuryNode_Address_Is_Not_A_Contract","type":"error"},{"inputs":[],"name":"FoundationTreasuryNode_Caller_Not_Admin","type":"error"},{"inputs":[{"internalType":"uint256","name":"buyPrice","type":"uint256"}],"name":"NFTMarketBuyPrice_Cannot_Buy_At_Lower_Price","type":"error"},{"inputs":[],"name":"NFTMarketBuyPrice_Cannot_Buy_Unset_Price","type":"error"},{"inputs":[],"name":"NFTMarketBuyPrice_Cannot_Cancel_Unset_Price","type":"error"},{"inputs":[{"internalType":"address","name":"owner","type":"address"}],"name":"NFTMarketBuyPrice_Only_Owner_Can_Cancel_Price","type":"error"},{"inputs":[{"internalType":"address","name":"owner","type":"address"}],"name":"NFTMarketBuyPrice_Only_Owner_Can_Set_Price","type":"error"},{"inputs":[],"name":"NFTMarketBuyPrice_Price_Already_Set","type":"error"},{"inputs":[],"name":"NFTMarketBuyPrice_Price_Too_High","type":"error"},{"inputs":[{"internalType":"address","name":"seller","type":"address"}],"name":"NFTMarketBuyPrice_Seller_Mismatch","type":"error"},{"inputs":[],"name":"NFTMarketCore_FETH_Address_Is_Not_A_Contract","type":"error"},{"inputs":[],"name":"NFTMarketCore_Only_FETH_Can_Transfer_ETH","type":"error"},{"inputs":[],"name":"NFTMarketCore_Seller_Not_Found","type":"error"},{"inputs":[],"name":"NFTMarketFees_Address_Does_Not_Support_IRoyaltyRegistry","type":"error"},{"inputs":[],"name":"NFTMarketOffer_Cannot_Be_Made_While_In_Auction","type":"error"},{"inputs":[{"internalType":"uint256","name":"currentOfferAmount","type":"uint256"}],"name":"NFTMarketOffer_Offer_Below_Min_Amount","type":"error"},{"inputs":[{"internalType":"uint256","name":"expiry","type":"uint256"}],"name":"NFTMarketOffer_Offer_Expired","type":"error"},{"inputs":[{"internalType":"address","name":"currentOfferFrom","type":"address"}],"name":"NFTMarketOffer_Offer_From_Does_Not_Match","type":"error"},{"inputs":[{"internalType":"uint256","name":"minOfferAmount","type":"uint256"}],"name":"NFTMarketOffer_Offer_Must_Be_At_Least_Min_Amount","type":"error"},{"inputs":[],"name":"NFTMarketOffer_Provided_Contract_And_TokenId_Count_Must_Match","type":"error"},{"inputs":[],"name":"NFTMarketOffer_Reason_Required","type":"error"},{"inputs":[{"internalType":"uint256","name":"auctionId","type":"uint256"}],"name":"NFTMarketReserveAuction_Already_Listed","type":"error"},{"inputs":[{"internalType":"uint256","name":"minAmount","type":"uint256"}],"name":"NFTMarketReserveAuction_Bid_Must_Be_At_Least_Min_Amount","type":"error"},{"inputs":[],"name":"NFTMarketReserveAuction_Cannot_Admin_Cancel_Without_Reason","type":"error"},{"inputs":[{"internalType":"uint256","name":"reservePrice","type":"uint256"}],"name":"NFTMarketReserveAuction_Cannot_Bid_Lower_Than_Reserve_Price","type":"error"},{"inputs":[{"internalType":"uint256","name":"endTime","type":"uint256"}],"name":"NFTMarketReserveAuction_Cannot_Bid_On_Ended_Auction","type":"error"},{"inputs":[],"name":"NFTMarketReserveAuction_Cannot_Bid_On_Nonexistent_Auction","type":"error"},{"inputs":[],"name":"NFTMarketReserveAuction_Cannot_Cancel_Nonexistent_Auction","type":"error"},{"inputs":[],"name":"NFTMarketReserveAuction_Cannot_Finalize_Already_Settled_Auction","type":"error"},{"inputs":[{"internalType":"uint256","name":"endTime","type":"uint256"}],"name":"NFTMarketReserveAuction_Cannot_Finalize_Auction_In_Progress","type":"error"},{"inputs":[],"name":"NFTMarketReserveAuction_Cannot_Rebid_Over_Outstanding_Bid","type":"error"},{"inputs":[],"name":"NFTMarketReserveAuction_Cannot_Update_Auction_In_Progress","type":"error"},{"inputs":[{"internalType":"uint256","name":"maxDuration","type":"uint256"}],"name":"NFTMarketReserveAuction_Exceeds_Max_Duration","type":"error"},{"inputs":[{"internalType":"uint256","name":"extensionDuration","type":"uint256"}],"name":"NFTMarketReserveAuction_Less_Than_Extension_Duration","type":"error"},{"inputs":[],"name":"NFTMarketReserveAuction_Must_Set_Non_Zero_Reserve_Price","type":"error"},{"inputs":[{"internalType":"address","name":"seller","type":"address"}],"name":"NFTMarketReserveAuction_Not_Matching_Seller","type":"error"},{"inputs":[{"internalType":"address","name":"owner","type":"address"}],"name":"NFTMarketReserveAuction_Only_Owner_Can_Update_Auction","type":"error"},{"inputs":[],"name":"NFTMarketReserveAuction_Price_Already_Set","type":"error"},{"inputs":[],"name":"NFTMarketReserveAuction_Too_Much_Value_Provided","type":"error"},{"anonymous":False,"inputs":[{"indexed":True,"internalType":"address","name":"nftContract","type":"address"},{"indexed":True,"internalType":"uint256","name":"tokenId","type":"uint256"},{"indexed":True,"internalType":"address","name":"seller","type":"address"},{"indexed":False,"internalType":"address","name":"buyer","type":"address"},{"indexed":False,"internalType":"uint256","name":"protocolFee","type":"uint256"},{"indexed":False,"internalType":"uint256","name":"creatorFee","type":"uint256"},{"indexed":False,"internalType":"uint256","name":"sellerRev","type":"uint256"}],"name":"BuyPriceAccepted","type":"event"},{"anonymous":False,"inputs":[{"indexed":True,"internalType":"address","name":"nftContract","type":"address"},{"indexed":True,"internalType":"uint256","name":"tokenId","type":"uint256"}],"name":"BuyPriceCanceled","type":"event"},{"anonymous":False,"inputs":[{"indexed":True,"internalType":"address","name":"nftContract","type":"address"},{"indexed":True,"internalType":"uint256","name":"tokenId","type":"uint256"}],"name":"BuyPriceInvalidated","type":"event"},{"anonymous":False,"inputs":[{"indexed":True,"internalType":"address","name":"nftContract","type":"address"},{"indexed":True,"internalType":"uint256","name":"tokenId","type":"uint256"},{"indexed":True,"internalType":"address","name":"seller","type":"address"},{"indexed":False,"internalType":"uint256","name":"price","type":"uint256"}],"name":"BuyPriceSet","type":"event"},{"anonymous":False,"inputs":[{"indexed":True,"internalType":"address","name":"nftContract","type":"address"},{"indexed":True,"internalType":"uint256","name":"tokenId","type":"uint256"},{"indexed":False,"internalType":"address","name":"buyReferrer","type":"address"},{"indexed":False,"internalType":"uint256","name":"buyReferrerProtocolFee","type":"uint256"},{"indexed":False,"internalType":"uint256","name":"buyReferrerSellerFee","type":"uint256"}],"name":"BuyReferralPaid","type":"event"},{"anonymous":False,"inputs":[{"indexed":False,"internalType":"uint8","name":"version","type":"uint8"}],"name":"Initialized","type":"event"},{"anonymous":False,"inputs":[{"indexed":True,"internalType":"address","name":"nftContract","type":"address"},{"indexed":True,"internalType":"uint256","name":"tokenId","type":"uint256"},{"indexed":True,"internalType":"address","name":"buyer","type":"address"},{"indexed":False,"internalType":"address","name":"seller","type":"address"},{"indexed":False,"internalType":"uint256","name":"protocolFee","type":"uint256"},{"indexed":False,"internalType":"uint256","name":"creatorFee","type":"uint256"},{"indexed":False,"internalType":"uint256","name":"sellerRev","type":"uint256"}],"name":"OfferAccepted","type":"event"},{"anonymous":False,"inputs":[{"indexed":True,"internalType":"address","name":"nftContract","type":"address"},{"indexed":True,"internalType":"uint256","name":"tokenId","type":"uint256"},{"indexed":False,"internalType":"string","name":"reason","type":"string"}],"name":"OfferCanceledByAdmin","type":"event"},{"anonymous":False,"inputs":[{"indexed":True,"internalType":"address","name":"nftContract","type":"address"},{"indexed":True,"internalType":"uint256","name":"tokenId","type":"uint256"}],"name":"OfferInvalidated","type":"event"},{"anonymous":False,"inputs":[{"indexed":True,"internalType":"address","name":"nftContract","type":"address"},{"indexed":True,"internalType":"uint256","name":"tokenId","type":"uint256"},{"indexed":True,"internalType":"address","name":"buyer","type":"address"},{"indexed":False,"internalType":"uint256","name":"amount","type":"uint256"},{"indexed":False,"internalType":"uint256","name":"expiration","type":"uint256"}],"name":"OfferMade","type":"event"},{"anonymous":False,"inputs":[{"indexed":True,"internalType":"uint256","name":"auctionId","type":"uint256"},{"indexed":True,"internalType":"address","name":"bidder","type":"address"},{"indexed":False,"internalType":"uint256","name":"amount","type":"uint256"},{"indexed":False,"internalType":"uint256","name":"endTime","type":"uint256"}],"name":"ReserveAuctionBidPlaced","type":"event"},{"anonymous":False,"inputs":[{"indexed":True,"internalType":"uint256","name":"auctionId","type":"uint256"}],"name":"ReserveAuctionCanceled","type":"event"},{"anonymous":False,"inputs":[{"indexed":True,"internalType":"uint256","name":"auctionId","type":"uint256"},{"indexed":False,"internalType":"string","name":"reason","type":"string"}],"name":"ReserveAuctionCanceledByAdmin","type":"event"},{"anonymous":False,"inputs":[{"indexed":True,"internalType":"address","name":"seller","type":"address"},{"indexed":True,"internalType":"address","name":"nftContract","type":"address"},{"indexed":True,"internalType":"uint256","name":"tokenId","type":"uint256"},{"indexed":False,"internalType":"uint256","name":"duration","type":"uint256"},{"indexed":False,"internalType":"uint256","name":"extensionDuration","type":"uint256"},{"indexed":False,"internalType":"uint256","name":"reservePrice","type":"uint256"},{"indexed":False,"internalType":"uint256","name":"auctionId","type":"uint256"}],"name":"ReserveAuctionCreated","type":"event"},{"anonymous":False,"inputs":[{"indexed":True,"internalType":"uint256","name":"auctionId","type":"uint256"},{"indexed":True,"internalType":"address","name":"seller","type":"address"},{"indexed":True,"internalType":"address","name":"bidder","type":"address"},{"indexed":False,"internalType":"uint256","name":"protocolFee","type":"uint256"},{"indexed":False,"internalType":"uint256","name":"creatorFee","type":"uint256"},{"indexed":False,"internalType":"uint256","name":"sellerRev","type":"uint256"}],"name":"ReserveAuctionFinalized","type":"event"},{"anonymous":False,"inputs":[{"indexed":True,"internalType":"uint256","name":"auctionId","type":"uint256"}],"name":"ReserveAuctionInvalidated","type":"event"},{"anonymous":False,"inputs":[{"indexed":True,"internalType":"uint256","name":"auctionId","type":"uint256"},{"indexed":False,"internalType":"uint256","name":"reservePrice","type":"uint256"}],"name":"ReserveAuctionUpdated","type":"event"},{"anonymous":False,"inputs":[{"indexed":True,"internalType":"address","name":"user","type":"address"},{"indexed":False,"internalType":"uint256","name":"amount","type":"uint256"}],"name":"WithdrawalToFETH","type":"event"},{"inputs":[{"internalType":"address","name":"nftContract","type":"address"},{"internalType":"uint256","name":"tokenId","type":"uint256"},{"internalType":"address","name":"offerFrom","type":"address"},{"internalType":"uint256","name":"minAmount","type":"uint256"}],"name":"acceptOffer","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address[]","name":"nftContracts","type":"address[]"},{"internalType":"uint256[]","name":"tokenIds","type":"uint256[]"},{"internalType":"string","name":"reason","type":"string"}],"name":"adminCancelOffers","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"auctionId","type":"uint256"},{"internalType":"string","name":"reason","type":"string"}],"name":"adminCancelReserveAuction","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"nftContract","type":"address"},{"internalType":"uint256","name":"tokenId","type":"uint256"},{"internalType":"uint256","name":"maxPrice","type":"uint256"}],"name":"buy","outputs":[],"stateMutability":"payable","type":"function"},{"inputs":[{"internalType":"address","name":"nftContract","type":"address"},{"internalType":"uint256","name":"tokenId","type":"uint256"},{"internalType":"uint256","name":"maxPrice","type":"uint256"},{"internalType":"address payable","name":"referrer","type":"address"}],"name":"buyV2","outputs":[],"stateMutability":"payable","type":"function"},{"inputs":[{"internalType":"address","name":"nftContract","type":"address"},{"internalType":"uint256","name":"tokenId","type":"uint256"}],"name":"cancelBuyPrice","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"auctionId","type":"uint256"}],"name":"cancelReserveAuction","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"nftContract","type":"address"},{"internalType":"uint256","name":"tokenId","type":"uint256"},{"internalType":"uint256","name":"reservePrice","type":"uint256"}],"name":"createReserveAuction","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"auctionId","type":"uint256"}],"name":"finalizeReserveAuction","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"nftContract","type":"address"},{"internalType":"uint256","name":"tokenId","type":"uint256"}],"name":"getBuyPrice","outputs":[{"internalType":"address","name":"seller","type":"address"},{"internalType":"uint256","name":"price","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"nftContract","type":"address"},{"internalType":"uint256","name":"tokenId","type":"uint256"},{"internalType":"uint256","name":"price","type":"uint256"}],"name":"getFeesAndRecipients","outputs":[{"internalType":"uint256","name":"protocolFee","type":"uint256"},{"internalType":"uint256","name":"creatorRev","type":"uint256"},{"internalType":"address payable[]","name":"creatorRecipients","type":"address[]"},{"internalType":"uint256[]","name":"creatorShares","type":"uint256[]"},{"internalType":"uint256","name":"sellerRev","type":"uint256"},{"internalType":"address payable","name":"owner","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"getFethAddress","outputs":[{"internalType":"address","name":"fethAddress","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"getFoundationTreasury","outputs":[{"internalType":"address payable","name":"treasuryAddress","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"nftContract","type":"address"},{"internalType":"uint256","name":"tokenId","type":"uint256"}],"name":"getImmutableRoyalties","outputs":[{"internalType":"address payable[]","name":"recipients","type":"address[]"},{"internalType":"uint256[]","name":"splitPerRecipientInBasisPoints","type":"uint256[]"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint256","name":"auctionId","type":"uint256"}],"name":"getMinBidAmount","outputs":[{"internalType":"uint256","name":"minimum","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"nftContract","type":"address"},{"internalType":"uint256","name":"tokenId","type":"uint256"}],"name":"getMinOfferAmount","outputs":[{"internalType":"uint256","name":"minimum","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"nftContract","type":"address"},{"internalType":"uint256","name":"tokenId","type":"uint256"},{"internalType":"address payable","name":"creator","type":"address"}],"name":"getMutableRoyalties","outputs":[{"internalType":"address payable[]","name":"recipients","type":"address[]"},{"internalType":"uint256[]","name":"splitPerRecipientInBasisPoints","type":"uint256[]"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"nftContract","type":"address"},{"internalType":"uint256","name":"tokenId","type":"uint256"}],"name":"getOffer","outputs":[{"internalType":"address","name":"buyer","type":"address"},{"internalType":"uint256","name":"expiration","type":"uint256"},{"internalType":"uint256","name":"amount","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"nftContract","type":"address"},{"internalType":"uint256","name":"tokenId","type":"uint256"}],"name":"getOfferReferrer","outputs":[{"internalType":"address payable","name":"referrer","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint256","name":"auctionId","type":"uint256"}],"name":"getReserveAuction","outputs":[{"components":[{"internalType":"address","name":"nftContract","type":"address"},{"internalType":"uint256","name":"tokenId","type":"uint256"},{"internalType":"address payable","name":"seller","type":"address"},{"internalType":"uint256","name":"duration","type":"uint256"},{"internalType":"uint256","name":"extensionDuration","type":"uint256"},{"internalType":"uint256","name":"endTime","type":"uint256"},{"internalType":"address payable","name":"bidder","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"}],"internalType":"struct NFTMarketReserveAuction.ReserveAuction","name":"auction","type":"tuple"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint256","name":"auctionId","type":"uint256"}],"name":"getReserveAuctionBidReferrer","outputs":[{"internalType":"address payable","name":"referrer","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"nftContract","type":"address"},{"internalType":"uint256","name":"tokenId","type":"uint256"}],"name":"getReserveAuctionIdFor","outputs":[{"internalType":"uint256","name":"auctionId","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"getRoyaltyRegistry","outputs":[{"internalType":"address","name":"registry","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"nftContract","type":"address"},{"internalType":"uint256","name":"tokenId","type":"uint256"}],"name":"getTokenCreator","outputs":[{"internalType":"address payable","name":"creator","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"initialize","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"nftContract","type":"address"},{"internalType":"uint256","name":"tokenId","type":"uint256"},{"internalType":"uint256","name":"amount","type":"uint256"}],"name":"makeOffer","outputs":[{"internalType":"uint256","name":"expiration","type":"uint256"}],"stateMutability":"payable","type":"function"},{"inputs":[{"internalType":"address","name":"nftContract","type":"address"},{"internalType":"uint256","name":"tokenId","type":"uint256"},{"internalType":"uint256","name":"amount","type":"uint256"},{"internalType":"address payable","name":"referrer","type":"address"}],"name":"makeOfferV2","outputs":[{"internalType":"uint256","name":"expiration","type":"uint256"}],"stateMutability":"payable","type":"function"},{"inputs":[{"internalType":"uint256","name":"auctionId","type":"uint256"}],"name":"placeBid","outputs":[],"stateMutability":"payable","type":"function"},{"inputs":[{"internalType":"uint256","name":"auctionId","type":"uint256"},{"internalType":"uint256","name":"amount","type":"uint256"},{"internalType":"address payable","name":"referrer","type":"address"}],"name":"placeBidV2","outputs":[],"stateMutability":"payable","type":"function"},{"inputs":[{"internalType":"address","name":"nftContract","type":"address"},{"internalType":"uint256","name":"tokenId","type":"uint256"},{"internalType":"uint256","name":"price","type":"uint256"}],"name":"setBuyPrice","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"auctionId","type":"uint256"},{"internalType":"uint256","name":"reservePrice","type":"uint256"}],"name":"updateReserveAuction","outputs":[],"stateMutability":"nonpayable","type":"function"},{"stateMutability":"payable","type":"receive"}]
    self.contract = w3.eth.contract(address="0xcDA72070E455bb31C7690a170224Ce43623d0B6f", abi=self.abi)
    self.poll_filter = self.contract.events.BuyPriceAccepted.createFilter(fromBlock="latest")

    self.db = db
    with db.begin() as txn:
      self.block = json.loads(txn.get(b"foundation_block"))

    self.start_block = w3.eth.block_number
    self.i = 0
    self.step = 10_000
    self.crawl_finished = False

  def extract_addresses(self, entries):
    addresses = []

    for entry in entries:
      args = entry["args"]

      address = args["nftContract"]
      if address not in addresses and address != web3.constants.ADDRESS_ZERO:
        addresses.append(address)

    return addresses

  async def find_addresses(self):
    if self.crawl_finished:
      entries = []
    else:
      fromBlock = self.block + self.i * self.step
      toBlock = self.block + (self.i + 1) * self.step
      if toBlock > self.start_block:
        toBlock = self.start_block

      with self.db.begin(write=True) as txn:
        txn.put(b"foundation_block", json.dumps(fromBlock).encode())

      try:
        crawl_filter = self.contract.events.BuyPriceAccepted.createFilter(fromBlock=fromBlock, toBlock=toBlock)
        entries = crawl_filter.get_all_entries()
      except ValueError as e:
        if "message" in e.args[0] and e.args[0]["message"] == "query returned more than 10000 results":
          self.step = self.step * 4 // 5
          return await self.find_addresses()
        else:
          raise e

      if toBlock == self.start_block:
        self.crawl_finished = True

      self.i += 1

    entries.extend(self.poll_filter.get_new_entries())

    return self.extract_addresses(entries)

  async def sleep(self):
    if self.crawl_finished:
      await asyncio.sleep(10)
    else:
      await asyncio.sleep(1)


class Forta:
  def __init__(self):
    transport = AIOHTTPTransport(url="https://api.forta.network/graphql")

    self.client = Client(
      transport=transport,
      fetch_schema_from_transport=True,
      execute_timeout=300,
    )

  async def connect(self):
    retry_connect = backoff.on_exception(
      backoff.expo,
      Exception,
      max_value=300,
    )
    retry_execute = backoff.on_exception(
      backoff.expo,
      Exception,
      max_tries=3,
      giveup=lambda e: isinstance(e, TransportQueryError),
    )
    self.session = await self.client.connect_async(
      reconnecting=True,
      retry_connect=retry_connect,
      retry_execute=retry_execute,
    )

  async def close(self):
    await self.client.close_async()

  async def get_alerts(self, alerts_input):
    gql_query = gql("""
      query Alerts($input: AlertsInput) {
        alerts(input: $input) {
          pageInfo {
            hasNextPage
            endCursor {
              alertId
              blockNumber
            }
          }
          alerts {
            alertId
            severity
            name
            description
          }
        }
      }
    """)

    results = []

    try:
      while True:
        result = await self.session.execute(gql_query, variable_values={
          "input": alerts_input,
        })
        results.append(result["alerts"]["alerts"])

        pageInfo = result["alerts"]["pageInfo"]
        if pageInfo["hasNextPage"]:
          alerts_input["after"] = pageInfo["endCursor"]
        else:
          break
    except asyncio.exceptions.TimeoutError:
      if len(results) == 0:
        results = [[None]]
    except asyncio.exceptions.CancelledError:
      if len(results) == 0:
        results = [[None]]

    alerts = [alert for alerts in results for alert in alerts]

    return alerts


def source_to_platform(source):
  if source == "Wyvern":
    return "OpenSea"
  elif source == "Seaport":
    return "OpenSea"
  elif source == "LooksRare":
    return "LooksRare"
  elif source == "Rarible":
    return "Rarible"
  elif source == "Foundation":
    return "Foundation"

def source_to_position(source):
  if source == "Wyvern":
    return 3
  elif source == "Seaport":
    return 0
  elif source == "LooksRare":
    return 1
  elif source == "Rarible":
    return 4
  elif source == "Foundation":
    return 2

async def query_alert_data(forta, source, addresses):
  progress_event = asyncio.Event()

  def process_row(address, alert):
    if alert == None:
      return None
    else:
      return {
        "asset": address,
        "platform": source_to_platform(source),
        "alert_id": alert["alertId"],
        "severity": alert["severity"],
        "name": alert["name"].replace("\00", ""),
        "description": alert["description"].replace("\00", ""),
      }

  async def query_by_address(address, progress):
    data = []

    for bot in BOTS:
      alerts = await forta.get_alerts({
        "addresses": [address],
        "bots": [bot],
        "first": 7_000,
        "severities": ["LOW", "MEDIUM", "HIGH", "CRITICAL"],
      })
      data.extend([process_row(address, alert) for alert in alerts])
      progress.update(1)

    if len(data) == 0:
      data = [{
        "asset": address,
        "platform": source_to_platform(source),
        "alert_id": None,
        "severity": "SAFE",
        "name": None,
        "description": None,
      }]
    data = list(filter(lambda row: row != None, data))

    return data

  batch_size = 10
  num_batches = math.ceil(len(addresses) / batch_size)
  batches = [addresses[i*batch_size:(i+1)*batch_size] for i in range(num_batches)]

  progress = tqdm(
    total=len(addresses) * len(BOTS),
    desc=f"{source} alerts",
    position=source_to_position(source),
    leave=False,
  )
  data = []
  for batch in batches:
    tasks = [asyncio.create_task(query_by_address(address, progress)) for address in batch]
    results = await asyncio.gather(*tasks)
    for result in results:
      data.extend(result)

  progress.close()

  return data

def create_snapshot(source, data):
  if len(data) == 0:
    return

  stamp = int(datetime.now().timestamp() * 1000)
  group = math.floor(stamp / 1000000) * 1000000

  folder = f"cache/snapshots/{group:06}"
  filename = f"snapshot-{stamp:06}.csv"

  if not os.path.isdir(folder):
    os.mkdir(folder)

  with open(f"{folder}/{filename}", "w", newline="") as output:
    writer = csv.DictWriter(output, fieldnames=FIELDNAMES, escapechar="\\")
    writer.writeheader()
    writer.writerows(data)
  
  tqdm.write(f"{source}: Output {filename}")

def filter_used_addresses(db, addresses):
  with db.begin() as txn:
    used_addresses = json.loads(txn.get(b"used_addresses"))

  return list(filter(lambda a: a not in used_addresses, addresses))

def update_used_addresses(db, addresses):
  with db.begin(write=True) as txn:
    used_addresses = json.loads(txn.get(b"used_addresses"))
    used_addresses = list(set(used_addresses + addresses))
    txn.put(b"used_addresses", json.dumps(used_addresses).encode())


async def main():
  print("Data collection starting...")

  if not os.path.isdir("cache"):
    os.mkdir("cache")

  if not os.path.isdir("cache/snapshots"):
    os.mkdir("cache/snapshots")

  w3 = Web3(Web3.HTTPProvider(os.environ["INFURA_MAINNET_ENDPOINT"]))
  db = lmdb.open("cache/store", max_dbs=1)

  with db.begin(write=True) as txn:
    if not txn.get(b"used_addresses"):
      txn.put(b"used_addresses", json.dumps([]).encode())

    if not txn.get(b"wyvern_block"):
      txn.put(b"wyvern_block", json.dumps(14220913).encode())

    if not txn.get(b"seaport_block"):
      txn.put(b"seaport_block", json.dumps(14946474).encode())

    if not txn.get(b"looksrare_block"):
      txn.put(b"looksrare_block", json.dumps(13885625).encode())

    if not txn.get(b"rarible_block"):
      txn.put(b"rarible_block", json.dumps(12617828).encode())

    if not txn.get(b"foundation_block"):
      txn.put(b"foundation_block", json.dumps(11648710).encode())

  wyvern = Wyvern(w3, db)
  seaport = Seaport(w3, db)
  looksrare = LooksRare(w3, db)
  rarible = Rarible(w3, db)
  foundation = Foundation(w3, db)

  forta = Forta()
  await forta.connect()

  async def query_contract(contract, source):
    while True:
      addresses = await contract.find_addresses()
      addresses = filter_used_addresses(db, addresses)
      if len(addresses) > 0:
        tqdm.write(f"{source}: Retrieved {len(addresses)} addresses")
        data = await query_alert_data(forta, source, addresses)
        create_snapshot(source, data)
        update_used_addresses(db, addresses)
      await contract.sleep()

  async def query_wyvern():
    while True:
      entries = await wyvern.find_addresses()
      tqdm.write(f"Wyvern: {entries}")
      await wyvern.sleep()

  async def query_rarible():
    while True:
      entries = await rarible.find_addresses()
      tqdm.write(f"Rarible: {entries}")
      await rarible.sleep()

  @atexit.register
  def close():
    asyncio.run(forta.close())

  await asyncio.gather(
    # asyncio.create_task(query_wyvern()),
    asyncio.create_task(query_contract(seaport, "Seaport")),
    asyncio.create_task(query_contract(looksrare, "LooksRare")),
    # asyncio.create_task(query_rarible()),
    asyncio.create_task(query_contract(foundation, "Foundation")),
  )

if __name__ == "__main__":
  asyncio.run(main())
