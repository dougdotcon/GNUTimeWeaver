import hashlib,json
def validate(hashes,ids,groups=1):
 if groups!=1: return 'G2L0M_MULTIPLE_CACHE_GROUPS_NOT_SUPPORTED'
 if len(ids)<len(hashes): return 'G2L0M_INSUFFICIENT_PHYSICAL_BLOCK_IDS'
 if any(i<0 or i>=2529 for i in ids): return 'G2L0M_PHYSICAL_BLOCK_ID_OUT_OF_RANGE'
 return 'PASS'
assert validate(list(range(7)),list(range(8)))=='PASS'
assert validate(list(range(7)),list(range(6)))=='G2L0M_INSUFFICIENT_PHYSICAL_BLOCK_IDS'
assert validate(list(range(7)),list(range(8)),2)=='G2L0M_MULTIPLE_CACHE_GROUPS_NOT_SUPPORTED'
print('G2L0M preflight PASS')
