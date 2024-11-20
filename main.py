import requests
from math import ceil
import json
import time
import matplotlib.pyplot as plt
from config import TOKEN_HASH, MIN_TOKEN_VALUE, WALLETS_AMOUNT, TOP
from params import PAGE_SIZE, EXPECTED_MESSAGE
LOG = ''


def page_counter():
    return ceil(WALLETS_AMOUNT / PAGE_SIZE)


def token_distributors(token_hash, pages): 
    # https://docs.solana.fm/reference/get_token_accounts_for_token_mint#section-this-endpoint-returns-you-a-paginated-list-of-token-accounts-owned-by-the-provided-token-mint
    holders_addresses = []
    for page in range(1, pages+1):
        url = f'https://api.solana.fm/v1/tokens/{token_hash}/holders?page={page}&pageSize={PAGE_SIZE}'
        headers = {"accept": "application/json"}
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            token_holders = data.get('tokenAccounts', [])
            for holder in token_holders:
                owner_address = holder.get('info', {}).get('owner')
                if owner_address:
                    holders_addresses.append(owner_address)
            if len(holders_addresses) >= WALLETS_AMOUNT:
                break
        except:
            break
    return holders_addresses[0:WALLETS_AMOUNT]


def wallet_tokens(address):
    # https://docs.solana.fm/reference/get_tokens_owned_by_account_handler
    url = f'https://api.solana.fm/v1/addresses/{address}/tokens'
    headers = {"accept": "application/json"}
    wallet_assets = {}
    global LOG
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        print(f'--LOG: func wallet_tokens() STATUS_CODE[{response.status_code}]')
        LOG += f'--LOG: func wallet_tokens() STATUS_CODE[{response.status_code}]\n'
    except:
        print(f'--LOG: func wallet_tokens() STATUS_CODE[{response.status_code}]')
        LOG += f'--LOG: func wallet_tokens() STATUS_CODE[{response.status_code}]\n'
        return wallet_assets
    if data.get('message') == EXPECTED_MESSAGE:
        print(f'--LOG: TO MANY TOKENS ACCOUNT')
        LOG += f'--LOG: TO MANY TOKENS ACCOUNT\n'
        time.sleep(10)
        return wallet_assets
    tokens = data.get('tokens', {})
    for token_address, holding_info in tokens.items():
        token_balance = holding_info.get('balance')
        if not token_balance:
            continue
        token_info = get_token_info(token_address)
        token_name = token_info['name']
        token_price = token_info['price']
        token_value = token_balance * token_price
        wallet_assets[token_name] = {
                'price': token_price,
                'balance': token_balance,
                'value': token_value,
                'contract': token_address
            }
        print(f'--LOG: ${token_name} ADDED TO WALLET ASSETS')
        LOG += f'--LOG: ${token_name} ADDED TO WALLET ASSETS\n'
    return wallet_assets     


def get_token_info(token_address): 
    url = f'https://api.dexscreener.com/latest/dex/tokens/{token_address}'
    global LOG
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        token_name = data['pairs'][0]['baseToken']['symbol']
        token_usd_price = float(data['pairs'][0]['priceUsd'])
        print(f'--LOG: func get_token_info() STATUS_CODE[{response.status_code}]')
        LOG += f'--LOG: func get_token_info() STATUS_CODE[{response.status_code}\n]'
    except:
        token_name = token_address
        token_usd_price = 0
        print(f'--LOG: func get_token_info() STATUS_CODE[{response.status_code}]')
        LOG += f'--LOG: func get_token_info() STATUS_CODE[{response.status_code}]\n'
    token_info = {
        'name': token_name,
        'price': token_usd_price
    }
    time.sleep(0.65)
    return token_info


def generate_file():
    global LOG
    WALLET_STATS = {}   
    pages = page_counter()
    wallets = token_distributors(TOKEN_HASH, pages)
    for wallet in wallets:
        if wallet not in WALLET_STATS:
            WALLET_STATS[wallet] = {}
        WALLET_STATS[wallet]['solscan'] = f'https://solscan.io/account/{wallet}'
        WALLET_STATS[wallet]['assets'] = wallet_tokens(wallet)
        print(f'--LOG: ADDRESS[{wallet}] PROCESSED\n')
        LOG += f'--LOG: ADDRESS[{wallet}] PROCESSED\n'
        LOG += '===========================================\n'
        time.sleep(5)       
    with open('data.json', 'w', encoding='utf-8') as file:
        json.dump(WALLET_STATS, file, indent=4, ensure_ascii=False)
    print('--LOG: FILE COMPILED!')
    LOG += '--LOG: FILE COMPILED!'


def token_overview():
    with open('data.json', 'r', encoding='utf-8') as file:
        data = json.load(file)    
    STATISTICS = {}
    for wallet_address, wallet_data in data.items():
        for token_name, token_data in wallet_data['assets'].items():
            price = token_data['price']
            contract = token_data['contract']
            value = token_data['value']
            if value >= MIN_TOKEN_VALUE:
                if token_name not in STATISTICS:
                    STATISTICS[token_name] = {
                        'price': price,
                        'rate': 0,
                        'holders': [],
                        'contract': contract
                    }
                STATISTICS[token_name]['rate'] += 1
                if wallet_address not in STATISTICS[token_name]['holders']:
                    STATISTICS[token_name]['holders'].append(wallet_address)
    SORTED_STATISTICS = dict(sorted(STATISTICS.items(), key=lambda item: item[1]['rate'], reverse=True))
    with open('stat.json', 'w', encoding='utf-8') as file:
        json.dump(SORTED_STATISTICS, file, indent=4, ensure_ascii=False)
    return SORTED_STATISTICS


def token_diagram(statistic):
    categories = []
    values = []
    for token_name, token_data in statistic.items():
        categories.append(token_name)
        values.append(token_data['rate'])
    plt.style.use('dark_background') 
    fig, ax = plt.subplots()
    ax.set_facecolor('black') 
    fig.patch.set_facecolor('black')  
    ax.tick_params(colors='white')  
    ax.xaxis.label.set_color('white')  
    ax.yaxis.label.set_color('white')  
    ax.title.set_color('white')
    plt.bar(categories[0:TOP], values[0:TOP], color='white')
    plt.title('ZZER0X TOKEN STATISTICS | Telegram: @shitshiller')
    plt.xlabel('[TOKENS]')
    plt.ylabel('[RATE]')
    plt.xticks(rotation=45)
    plt.grid(True, which='both', axis='y', linestyle='--', color='gray', alpha=0.5)
    plt.grid(True, which='both', axis='x', linestyle='--', color='gray', alpha=0.5)
    plt.tight_layout()
    plt.show()


def main():
    global LOG
    generate_file()
    with open('log.txt', 'w', encoding='utf-8') as file:
        file.write(LOG)
    statistic = token_overview()
    token_diagram(statistic)
    

if __name__ == '__main__':
    main()