# Natural Language Toolkit: Language Model Vocabulary
#
# Copyright (C) 2001-2018 NLTK Project
# Author: Ilia Kurenkov <ilia.kurenkov@gmail.com>
# URL: <http://nltk.org/>
# For license information, see LICENSE.TXT
"""
Building a Vocabulary
---------------------

    >>> words = ['a', 'c', '-', 'd', 'c', 'a', 'b', 'r', 'a', 'c', 'd']
    >>> from nltk.lm import Vocabulary
    >>> vocab = Vocabulary(words, unk_cutoff=2)

Tokens with counts greater than or equal to the cuttoff value will
be considered part of the vocabulary.

    >>> vocab['c']
    3
    >>> 'c' in vocab
    True
    >>> vocab['d']
    2
    >>> 'd' in vocab
    True

Tokens with frequency counts less than the cutoff value will be considered not
part of the vocabulary even though their entries in the count dictionary are
preserved.

    >>> vocab['b']
    1
    >>> 'b' in vocab
    False
    >>> vocab['aliens']
    0
    >>> 'aliens' in vocab
    False

Keeping the count entries for seen words allows us to change the cutoff value
without having to recalculate the counts.

    >>> vocab2 = Vocabulary(vocab.counts, unk_cutoff=1)
    >>> "b" in vocab2
    True

The cutoff value influences not only membership checking but also the result of
getting the size of the vocabulary using the built-in `len`.
Note that while the number of keys in the vocabulary's counter stays the same,
the items in the vocabulary differ depending on the cutoff.
We use `sorted` to demonstrate because it keeps the order consistent.

    >>> sorted(vocab2.counts)
    ['-', 'a', 'b', 'c', 'd', 'r']
    >>> sorted(vocab2)
    ['-', '<UNK>', 'a', 'b', 'c', 'd', 'r']
    >>> sorted(vocab.counts)
    ['-', 'a', 'b', 'c', 'd', 'r']
    >>> sorted(vocab)
    ['<UNK>', 'a', 'c', 'd']

In addition to items shown during its creation, the vocabulary stores a special
token that stands in for "unknown" itenms.
By default it's "<UNK>".

    >>> "<UNK>" in vocab
    True

We can look up words in a vocabulary using its `lookup` method.
"Unseen" words (with counts less than cutoff) are looked up as the unknown label.
If given one word (a string) as an input, this method will return a string.

    >>> vocab.lookup("a")
    'a'
    >>> vocab.lookup("aliens")
    '<UNK>'

If given a sequence, it will return an iterator over the looked up words.

    >>> list(vocab.lookup(["p", 'a', 'r', 'd', 'b', 'c']))
    ['<UNK>', 'a', '<UNK>', 'd', '<UNK>', 'c']

It's possible to update the counts after its creation.

    >>> vocab['b']
    1
    >>> vocab.update(["b", "b", "c"])
    >>> vocab['b']
    3

"""

from __future__ import unicode_literals

import sys
from functools import singledispatch
from collections import Counter, Iterable, Set
from itertools import chain

from nltk import compat


@singledispatch
def _dispatched_lookup(words, vocab):
    raise TypeError("Unsupported type for looking up in vocabulary: {0}".format(type(words)))


@_dispatched_lookup.register(Iterable)
def _(words, vocab):
    """Look up a sequence of words in the vocabulary.

    Returns an iterator over looked up words.

    """
    return (_dispatched_lookup(w, vocab) for w in words)


@_dispatched_lookup.register(str)
def _(word, vocab):
    """Looks up one word in the vocabulary."""
    return word if word in vocab else vocab.unk_label


@compat.python_2_unicode_compatible
class Vocabulary(object):
    """Stores language model vocabulary.

    Satisfies two common language modeling requirements for a vocabulary:
    - When checking membership and calculating its size, filters items
      by comparing their counts to a cutoff value.
    - Adds a special "unknown" token which unseen words are mapped to.

    >>> from nltk.lm import Vocabulary
    >>> vocab = Vocabulary(["a", "b", "c", "a", "b"], unk_cutoff=2)
    >>> "a" in vocab
    True
    >>> "c" in vocab
    False
    >>> sorted(vocab)
    ['<UNK>', 'a', 'b']
    >>> sorted(vocab.counts)
    ['a', 'b', 'c']

    """

    def __init__(self, counts=None, unk_cutoff=1, unk_label="<UNK>"):
        """Create a new Vocabulary.

        :param counts: Optional iterable or `collections.Counter` instance to
                       pre-seed the Vocabulary. In case it is iterable, counts
                       are calculated.
        :param int unk_cutoff: Words that occur less frequently than this value
                               are not considered part of the vocabulary.
        :param unk_label: Label for marking words not part of vocabulary.

        """
        if isinstance(counts, Counter):
            self.counts = counts
        else:
            self.counts = Counter()
            if isinstance(counts, Iterable):
                self.counts.update(counts)
        self.unk_label = unk_label
        if unk_cutoff < 1:
            raise ValueError("Cutoff value cannot be less than 1. Got: {0}".format(unk_cutoff))
        self._cutoff = unk_cutoff

    @property
    def cutoff(self):
        """Cutoff value.

        Items with count below this value are not considered part of vocabulary.

        """
        return self._cutoff

    def update(self, *counter_args, **counter_kwargs):
        """Update vocabulary counts.

        Wraps `collections.Counter.update` method.

        """
        self.counts.update(*counter_args, **counter_kwargs)

    def lookup(self, words):
        """Look up one or more words in the vocabulary.

        If passed one word as a string will return that word or `self.unk_label`.
        Otherwise will assume it was passed a sequence of words, will try to look
        each of them up and return an iterator over the looked up words.

        :param words: Word(s) to look up.
        :type words: Iterable(str) or str
        :rtype: generator(str) or str
        :raises: TypeError for types other than strings or iterables

        >>> from nltk.lm import Vocabulary
        >>> vocab = Vocabulary(["a", "b", "c", "a", "b"], unk_cutoff=2)
        >>> vocab.lookup("a")
        'a'
        >>> vocab.lookup("aliens")
        '<UNK>'
        >>> list(vocab.lookup(["a", "b", "c"]))
        ['a', 'b', '<UNK>']

        """
        return _dispatched_lookup(words, self)

    def __getitem__(self, item):
        return self._cutoff if item == self.unk_label else self.counts[item]

    def __contains__(self, item):
        """Only consider items with counts GE to cutoff as being in the
        vocabulary."""
        return self[item] >= self.cutoff

    def __iter__(self):
        """Building on membership check define how to iterate over
        vocabulary."""
        return chain((item for item in self.counts if item in self), [self.unk_label] if self.counts
                     else [])

    def __len__(self):
        """Computing size of vocabulary reflects the cutoff."""
        return sum(1 for _ in self)

    def __eq__(self, other):
        return (self.unk_label == other.unk_label and self.cutoff == other.cutoff and
                self.counts == other.counts)

    if sys.version_info[0] == 2:
        # see https://stackoverflow.com/a/35781654/4501212
        def __ne__(self, other):
            equal = self.__eq__(other)
            return equal if equal is NotImplemented else not equal

    def __str__(self):
        return "<{0} with cutoff={1} unk_label='{2}' and {3} items>".format(
            self.__class__.__name__, self.cutoff, self.unk_label, len(self))
