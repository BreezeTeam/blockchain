"""
block = {
    'index': 1,
    'timestamp': 1506057125.900785,
    'transactions': [
        {
            'sender': "8527147fe1f5426f9dd545de4b27ee00",
            'recipient': "a77f5cdfa2934df3954a5c7c7da5df1f",
            'amount': 5,
        }
    ],
    'proof': 324984774000,
    'previous_hash': "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824"
}
"""
import hashlib
from typing import *
from urllib.parse import urlparse
from uuid import uuid4

import aiohttp as aiohttp
from pydantic import BaseModel

from time import time


class Transaction(BaseModel):
    sender: str  # 发送者地址
    recipient: str  # 接收者地址
    amount: float  # 数量


class Response(BaseModel):
    code: int = 200
    msg: str = ''
    data: Union[List, Dict, Mapping, AnyStr, int, float] = None


class Block(BaseModel):
    index: int  # 块 索引
    timestamp: float  # 块生成时间锉
    transactions: List[Transaction]  # 块的交易列表
    proof: int  # 工作量证明
    previous_hash: str  # 前一个区块的hash


class Blockchain:
    def __init__(self):
        self.chain: List[Block] = []  # 当前的区块链
        self.current_transactions: List[Transaction] = []  # 当前交易

        # 创建一个创世区块
        self.new_block(proof=1, previous_hash=1)
        self.node_identifier = str(uuid4()).replace('-', '')

        # 用于分布式环境中 保存多个节点的信息
        self.nodes = set()

    def register_node(self, address):
        """
        将地址添加到 节点列表中
        :param address: http://192.168.0.5:5000
        :return:
        """
        parsed_url = urlparse(address)
        self.nodes.add(parsed_url.netloc)

    async def fetch(self, client, node):
        async with client.get(f'http://{node}/chain') as resp:
            assert resp.status == 200
            return await resp.json()

    async def resolve_conflicts(self):
        """
        区块链中最长的链作为共识
        :return:
        """
        new_chain = []
        max_length = len(self.chain)
        async with aiohttp.ClientSession() as client:
            for node in self.nodes:
                data = await self.fetch(client, node)
                chain = [Block(**i) for i in Response(**data).data]
                length = len(chain)
                if length > max_length and self.valid_chain(chain):
                    max_length = length
                    new_chain = chain

        if new_chain:
            self.chain = new_chain
            return True
        return False

    @property
    def node_id(self):
        """
        返回该节点的地址
        :return:
        """
        return self.node_identifier

    def proof_of_work(self, last_proof) -> int:
        """
        工作量证明机制
        查找一个 p1 使得 hash(pp1) 以 0000 开头
        其中 p 是上一个区块的证明,p1 是当前区块的证明
        :param last_proof:
        :return: 返回新的工作量证明
        """
        proof = 0
        while not self.valid_proof(last_proof, proof):
            proof += 1
        return proof

    @staticmethod
    def valid_proof(last_proof, proof):
        """
        验证 hash(last_proof,proof) 是否以 0000 开头
        :param last_proof:
        :param proof:
        :return:
        """
        guess = f'{last_proof}{proof}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:4] == "0000"

    def new_block(self, proof, previous_hash=None):
        """
        创建一个信息的块
        :param proof:
        :param previous_hash:
        :return:
        """
        block = Block(
            index=len(self.chain) + 1,  # 块索引
            timestamp=time(),  # 生成时间戳
            transactions=self.current_transactions,  # 包含的交易信息
            proof=proof,  # 工作量证明
            previous_hash=previous_hash or self.hash(self.chain[-1]),  # 前一个区块的hash值
        )
        self.current_transactions = []
        self.chain.append(block)
        return block

    def new_transactions(self, sender: str, recipient: str, amount: float) -> int:
        """
        生成交易信息,并返回记录该交易信息的待挖掘块索引
        :param sender: 发送者
        :param recipient: 接收者
        :param amount: 数量
        :return:
        """
        self.current_transactions.append(Transaction(
            sender=sender,
            recipient=recipient,
            amount=amount,
        ))
        return self.last_block.index + 1

    @staticmethod
    def hash(block: Block) -> str:
        """
        返回块的 sha-256 hash 值
        :param block:
        :return:
        """
        return hashlib.sha256(block.json().encode()).hexdigest()

    @property
    def last_block(self):
        """
        返回最后一个区块
        :return:
        """
        return self.chain[-1]

    def valid_chain(self, chain: List[Block]):
        last_block = chain[0]
        current_index = 1

        while current_index < len(chain):
            block = chain[current_index]
            if block.previous_hash != self.hash(last_block):
                return False
            if not self.valid_proof(last_block.proof, block.proof):
                return False

            last_block = block
            current_index += 1

        return True


blockchain = Blockchain()

__all__ = ["blockchain", "Transaction", "Response"]
