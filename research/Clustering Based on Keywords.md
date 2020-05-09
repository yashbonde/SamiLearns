# Topic Detection

The ideas noted here revolve around the problem of topic detection from keywords.

## Paper 1: [Topic Detection by Clustering Keywords (Warten et al.)](https://www.researchgate.net/publication/4374762_Topic_Detection_by_Clustering_Keywords)

### Distributions

We consider a collection of $n$ term occurrences $W$. Each term occurrence is an instance of exactly one term $t$ in $T = \{t_1,...,t_m\}$, and can be found in exactly one source document $d$ in a collection $C = \{d_1,...,d_M\}$. Let $n(d,t)$ be the number of occurrences of term $t$ in $d$, $n(t) = \sum_t n(d, t)$ be the number of occurrences of term $t$, and $N(d) = \sum_t n(d, t)$ the number of term occurrences in $d$.

Now we consider the natural probability distribution \(Q(d,t) = \frac{n(d,t)}{n}\), distribution \(Q(d) = \frac{N(d)}{n}\) and \(q(t) = \frac{n(t)}{n}\). These are the baseline probability distributions for everything that we will do in the remainder. In addition we have two important conditional probabilities
\[Q(d|t) = Q_t(d) = \frac{n(d,t)}{n(t)}\]
\[q(t|d) = q_d(t) = \frac{n(d,t)}{N(d)}\]

The suggestive notation \(Q(d|t)\) is used for the source distribution of \(t\) as it is the probability that a randomly selected occurrence of term \(t\) has source \(d\). Similarly, \(q(t|d)\), the term distribution of \(d\) is the probability that a randomly selected term occurrence from document \(d\) is an instance of term \(t\).

### Distributions of Co-occurring Terms

This kind of setup allows us to setup a markov chain on the set of documents and terms which will allow us to propogate the probability distributions from terms to documents and vica versa ver easily. So we say that given a term distribution \(p(t)\), we can get the document distribution \(P_p(d) = \sum_t Q(d|t)p(t)\), the probability to find a term occurance in document \(d\).

Similarly given a document distribution \(P(d)\) we can calculate that the probability of finding a term occurance in document \(d\) as \(p_P(t) = \sum_d q(t|d)P(d)\). Consider both one step Markov Chain evolutions, so combining these gives us a new distribution.
\[\overline{p}(t) = p_{P_p}(t) = \sum_d q(t|d)P(d) = \sum_{d,t'} q(t|d)Q(d|t')p(t')\]
where we consider the occurence probability \(p(t') = p(t|z)\) as degenerate, i.e. \(p(t') = 1\) iff \(t = z\). So the distribution of co-occuring terms \(\overline{p_z}(t) = \sum_d q(d|t)Q(d|z)\). This distribution is the weighted average of the term distributions of documents containing \(z\) where the weight is the probability \(Q(d|z)\) that a term occurrence in \(d\) is an occurrence of \(z\).

### Distances

One meteric for testing was the cosine similarity (distance becomes \(1 - cossim(i,j)\)) and the other main distance was the Jensen-Shannon divergence or information radius between two distributions \(p\) and \(q\), defined as
\[JS(p||q) = \frac{1}{2}D(p||m) + \frac{1}{2}D(q||m)\]
where \(m = \frac{p+q}{2}\) and term \(D(\cdot)\) is the Kullback-Leibler divergence defined as
\[D(p||q) = \sum_{i=1}^{n}p_i \log\big( \frac{p_i}{q_i} \big)\]
And against those we get two distances the document \(JSD_{doc} = JSD(Q_t, Q_s)\) and term based \(JSD_{term} = JSD(\overline{p_s}, \overline{p_t})\)
