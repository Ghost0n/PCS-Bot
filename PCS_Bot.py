# import the following dependencies
import json
from web3 import Web3
import time

bsc = 'https://data-seed-prebsc-1-s1.binance.org:8545'    
web3 = Web3(Web3.HTTPProvider(bsc))
if web3.isConnected():
    print('Connected to bsc testnet...')

# uniswap factory address and abi = pancakeswap factory
uniswap_factory = '0x6725F303b657a9451d8BA641348b6761A6CC7a17'  #testnet
uni_abi = open('§§§PATH TO FOLDER HERE§§§/uniswap_factory_abi.json')  #Don't forget to put your path to folder here
uniswap_factory_abi = json.load(uni_abi)
contract = web3.eth.contract(address=uniswap_factory, abi=uniswap_factory_abi)

#pancakeswap router abi 
panRouterContractAddress = '0x9Ac64Cc6e4415144C455BD8E4837Fea55603e5c3'    #testnet
pan_abi = open('§§§PATH TO FOLDER HERE§§§/panabi.json')  #Don't forget to put your path to folder here
panabi = json.load(pan_abi)
contractbuy = web3.eth.contract(address=panRouterContractAddress, abi=panabi)

spend = web3.toChecksumAddress("0xae13d989dac2f0debff460ac112a837c89baa7cd")   #WBNB_Testnet 
Busd = web3.toChecksumAddress("0x8301f2213c0eed49a7e28ae4c3e91722919b8b47")   #BUSD_Testnet 

def init():
    global wallet_address, sender_address, nonce, tokenToBuy, InitialPrice, maxPrice, amountOut, maxAmountIn, PrivateKeys, liq_wallet
    
    liq_wallet = ""                        #0.001 BNB to be transferred to the test liquidity wallet
    wallet_address = ""                    #TestNet Wallet 
    sender_address = web3.toChecksumAddress(wallet_address)                               
    PrivateKeys = ""      #private Keys
    nonce = web3.eth.get_transaction_count(sender_address)


    tokenToBuy = web3.toChecksumAddress("")

    #swapETHForExactTokens     
    amountOut = multDecimal(2)
    maxAmountIn = 0.1    #user input (in BNB)
    
def multDecimal(x):
    return int(x*10**18)
def divDecimal(x):
    return x/(10**18)

def price():
    [In,Out] = contractbuy.functions.getAmountsOut(multDecimal(0.001), [spend,tokenToBuy]).call()
    bnbIn = divDecimal(In)
    tokenOut = divDecimal(Out)
    price_bnb = bnbIn / tokenOut
    return price_bnb 

def convertToBnb(price_busd):
    [In,Out] = contractbuy.functions.getAmountsOut(multDecimal(price_busd), [Busd,spend]).call()
    return divDecimal(Out)

def DetectLiquidity(): 
     
     
    test = True
    try:    
        [In,Out] = contractbuy.functions.getAmountsOut(multDecimal(0.001), [spend,tokenToBuy]).call()
    except Exception as e:
        test = False

    if test == True:
        return True
    
      
    try:    
        contractbuy.functions.swapExactETHForTokens(
        0,
        [spend,tokenToBuy],
        web3.toChecksumAddress(liq_wallet),
        (int(time.time()) + 300)
        ).estimateGas({
        'from': web3.toChecksumAddress(liq_wallet),
        'value': web3.toWei(0.02,'ether'),
        'gasPrice': web3.toWei('7','gwei'),
        'nonce': web3.eth.get_transaction_count(web3.toChecksumAddress(liq_wallet)),
        })
    except Exception as e:
        return False

    return True 

def buy(amountOut,maxAmountIn):

    pancakeswap2_txn = contractbuy.functions.swapETHForExactTokens(
    amountOut, #Exact amount of token you want to receive - consider decimals!!!
    [spend,tokenToBuy],
    sender_address,
    (int(time.time()) + 300)
    ).buildTransaction({
    'from': sender_address,
    'value': web3.toWei(maxAmountIn,'ether'),#This is the maximum Token(BNB) amount you want to Swap from
    'gas': 5000000,
    'gasPrice': web3.toWei('10','gwei'),
    'nonce': nonce,
    })

    signed_txn = web3.eth.account.sign_transaction(pancakeswap2_txn, private_key=PrivateKeys)  #Private keys Testnet wallet
    tx_token = web3.eth.send_raw_transaction(signed_txn.rawTransaction)
    tx_status = web3.eth.wait_for_transaction_receipt(tx_token).status

    if (tx_status):
        print("Snipe was succesfull, bought: " + web3.toHex(tx_token))
        return 1
    else:
        return 0



def main():
    global wallet_address, sender_address, nonce, tokenToBuy, InitialPrice, maxPrice, amountOut, maxAmountIn, PrivateKeys, liq_wallet

    init()

    while (DetectLiquidity() == False):
        print("Liquidity Not provided yet...")    
        time.sleep(0.5)
   
    if (DetectLiquidity()):
        print('Liquidity Detected!\nInitiating the snipe...')
        i = 1
        while i <= 5:
            print("Buy Attempt: ",i)
            try:
                #time.sleep(3)  #to be reviewed
                                    
                InitialPrice = price()
                maxAmountIn = (divDecimal(amountOut) * InitialPrice) * 1.02   #setting slippage (for exp 2% is 1.02)

                t = buy(amountOut,maxAmountIn)
            except Exception as e:
                print("Transaction reverted by the contract..Retrying..")
                amountOut = multDecimal(divDecimal(amountOut) / 2)
                i += 1
                time.sleep(1)
                continue
            if t:
                break

            else:
                print("Transaction failed after block mined..Retrying..")
                amountOut = multDecimal(divDecimal(amountOut) / 2)
                i += 1
                time.sleep(1)
                continue

    uni_abi.close()
    pan_abi.close()



if __name__ == "__main__":
    main()
