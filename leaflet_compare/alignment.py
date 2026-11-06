from .text import similarity

def align(reference, revision):
    """Monotonic paragraph alignment. Explicit gaps beat unrelated substitutions.

    Adjacent lines are assembled in extraction; reordering/multi-column flow is out
    of scope. Return (reference, revision, similarity) tuples, including gaps.
    """
    n, m = len(reference), len(revision)
    dp = [[0.0]*(m+1) for _ in range(n+1)]
    back = {}
    for i in range(1,n+1): dp[i][0]=i*.55; back[i,0]='delete'
    for j in range(1,m+1): dp[0][j]=j*.55; back[0,j]='insert'
    for i in range(1,n+1):
        for j in range(1,m+1):
            score=similarity(reference[i-1].text,revision[j-1].text)
            choices=[(dp[i-1][j-1]+(1-score if score>=.45 else 1.2),'match'),
                     (dp[i-1][j]+.55,'delete'),(dp[i][j-1]+.55,'insert')]
            dp[i][j],back[i,j]=min(choices,key=lambda x:x[0])
    result=[]; i,j=n,m
    while i or j:
        action=back[i,j]
        if action=='match':
            a,b=reference[i-1],revision[j-1]; result.append((a,b,similarity(a.text,b.text))); i-=1;j-=1
        elif action=='delete': result.append((reference[i-1],None,0));i-=1
        else: result.append((None,revision[j-1],0));j-=1
    return list(reversed(result))
