import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
from typing import *

from blockchain import *

#  使用fastapi 实现网络节点
app = FastAPI()


@app.get('/mine')
def mine():
    """
    挖一个新区块
    1.计算工作量证明PoW
    2.通过新增一个交易授予矿工（自己）一个币
    3.构造新区块并将其添加到链中
    :return:
    """
    # 1.计算工作量证明PoW
    proof = blockchain.proof_of_work(blockchain.last_block.proof)
    # 2.通过新增一个交易授予矿工（自己）一个币
    blockchain.new_transactions(sender="0", recipient=blockchain.node_id, amount=1)
    # 3.构造新区块并将其添加到链中
    block = blockchain.new_block(proof, None)
    return Response(data=block, msg="New Block Forged")


@app.post('/transactions/new')
def new_transaction(transaction: Transaction):
    """
    创建一个新交易
    :return:
    """
    index = blockchain.new_transactions(transaction.sender, transaction.recipient, transaction.amount)
    return Response(msg=f"Transaction will be added to Block {index}")


@app.get('/chain', response_model=Response)
def full_chain():
    return Response(data=blockchain.chain)


@app.post("/nodes/register")
def register_node(nodes: List[str]):
    """
    注册别的节点
    :param nodes:
    :return:
    """
    for node in nodes:
        blockchain.register_node(node)
    return Response(msg="New nodes have been added", data=blockchain.nodes)


@app.get('/nodes/resolve')
async def consensus():
    replaced = await  blockchain.resolve_conflicts()

    if replaced:
        return Response(msg="Our chain was replaced", data=blockchain.chain)
    else:
        return Response(msg="Our chain is authoritative", data=blockchain.chain)


if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=5000)
