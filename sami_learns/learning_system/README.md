# How it works?

There are certain **serious** limitations to how the system operates as of now, we are only looking at the keywords based system. This is not what I had hoped for, but I have wasted too much time on the brain of it than actually shipping the damn thing. So I will just take the top paragraphs from the keywords, see which are the most dissimilar and use those as the text in the system.

The flow goes like this:
```
Step #1: gather the sentences and metadata
Step #2: create a simple n(d,t) matrix for only those paragraphs that have meta data information
Step #3: perform simple counting and basic aggregation when mulitple paragraphs per keyword overlap
Step #4: Identify all the sentences that need to be embedded in the sequence
Step #5: Perform distance based embedding on them (either cosine, euclidean, dotsimilarity)
Step #6: Merge all the information and create the return data object
```
