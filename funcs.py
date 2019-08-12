#!/usr/bin/env python
'''
Helper functions to get api data
'''
from concurrent.futures import ProcessPoolExecutor as PoolExecutor
import requests

MAX_WORKERS = 8

def latest_height(api):
    '''
    Get latest block height
    '''
    r = requests.get(f'{api}/blocks?limit=1')
    if r.status_code == 200:
        data = r.json().get('data')
        return data[0]['height']
    raise Exception('Unable to get latest height')

def get_blocks(api, num_blocks=100):
    '''
    Get past `NUM_BLOCKS` number of num_blocks
    '''
    r = requests.get(f'{api}/blocks?limit={num_blocks}')
    if r.status_code == 200:
        data = r.json().get('data')
        assert len(data) == num_blocks
        return data
    raise Exception('Unable to get blocks')

def get_txn(api, block_height):
    '''
    Get transactions for given block_height
    Called from `get_transactions`
    '''
    r = requests.get(f'{api}/blocks/{block_height}/transactions')
    if r.status_code == 200:
        data = r.json().get('data')
        return data
    raise Exception('Unable to get txns')

def get_challenges(api, num_challenges=100):
    '''
    Get past `LIMIT` number of challenges
    '''
    r = requests.get(f'{api}/challenges?limit={num_challenges}')
    if r.status_code == 200:
        data = r.json().get('data')
        assert len(data) == num_challenges
        return accumulate_results(data)
    raise Exception('Unable to get challenges')

def get_transactions(start, num_blocks=100):
    '''
    Get transactions for each block
    Starting from block height `LATEST_HEIGHT` by default and ending at start - num_blocks
    '''
    heights = range(start, start-num_blocks, -1)
    with PoolExecutor(max_workers=MAX_WORKERS) as executor:
        txns = {}
        for height, i in zip(heights, executor.map(get_txn, heights)):
            txns[height] = len(i)
    return txns

def get_hotspots(api):
    '''
    Get hotspots from the api
    '''
    r = requests.get(f'{api}/hotspots')
    if r.status_code == 200:
        data = r.json().get('data')
        return data
    raise Exception('Unable to get hotspots')

def get_accounts(api):
    '''
    Get accounts from the api
    '''
    r = requests.get(f'{api}/accounts')
    if r.status_code == 200:
        data = r.json().get('data')
        return data
    raise Exception('Unable to get accounts')

def accumulate_results(challenges):
    '''
    Return a dict list of challenge_id, num_successes, num_failures and num_untested
    '''
    results = []
    for challenge in challenges:
        path = challenge['pathElements']

        result = [element['result'] for element in path]
        length = len(result)
        num_untested = result.count('untested')

        gray = True if num_untested == length else False

        if gray:
            num_successes = 0
            num_failures = 0
            num_untested = 0
            dud = 1
            success = 0
        else:
            num_successes = result.count('success')
            num_failures = result.count('failure')
            num_untested = num_untested
            dud = 0
            success = 1 if num_successes == length else 0
        results.append({'id': challenge['id'],
                        'num_successes': num_successes,
                        'num_failures': num_failures,
                        'num_untested': num_untested,
                        'dud': dud,
                        'success': success})
    return results
