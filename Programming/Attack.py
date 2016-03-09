#!/usr/bin/python3
"""
import urllib
import urllib.error
import urllib.request
import multiprocessing.dummy
import sys

import operator

from itertools import islice
from itertools import repeat
from itertools import chain

from binascii import hexlify
from binascii import unhexlify

def grouper(iterable, n, fillvalue=None):
    "Collect data into fixed-length chunks or blocks"
    # grouper('ABCDEFG', 3, 'x') --> ABC DEF Gxx"
    args = [iter(iterable)] * n
    return zip_longest(*args, fillvalue=fillvalue)

#--------------------------------------------------------------
# padding oracle
#--------------------------------------------------------------
class PaddingOracle(object):
    block_size = 16
    hex_block_size = 2*block_size

    def __init__(self, targetURL, ct):
        self._targetURL = targetURL

        self._ct = ct

        self._numPTBlocks = int(len(self._ct)/self.block_size) - 1
        self._ptGuesses = [bytearray(self.block_size) for i in range(self._numPTBlocks)]


    def attack(self):
        #poolSZ = 64
        #pool = multiprocessing.Pool(poolSZ)

        for block in range(0, self._numPTBlocks):
            self._attack_block(block)

        return b''.join(self._ptGuesses)

    def _attack_block(self, block):
        poolSZ = 128
        pool = multiprocessing.dummy.Pool(poolSZ)

        for blockPos in reversed(range(self.block_size)):
            print("Guessing [{}][{}]".format(block, blockPos))

            res = pool.map(self.query,
                    ((islice(self._ct, block*self.block_size),
                     self._guess_block(block, blockPos, g),
                     islice(self._ct, (block+1)*self.block_size, (block+2)*self.block_size))

                    for g in range(128)))

            res = list(res)

            try:
                value = next(v for v,correct in enumerate(res) if correct)
            except StopIteration:
                print("Stopped")
                # This is the start of the pad at the end of the message
                value = next(v for v,correct in enumerate(res) if correct is None)

            print("Correctly guessed [{}][{}] = {}".format(block, blockPos, value))
            self._ptGuesses[block][blockPos] = value

    def _guess_block(self, block, blockPos, value):

        padLen = self.block_size - blockPos
        ctPos = block*self.block_size

        guessBlock = self._ptGuesses[block][:]
        guessBlock[blockPos:] = map(operator.xor, islice(guessBlock, blockPos, None), repeat(padLen))
        guessBlock[blockPos] = guessBlock[blockPos] ^ value
        guessBlock[:] = map(operator.xor, islice(guessBlock, None), islice(self._ct, ctPos, ctPos + self.block_size))
        #print(value)
        return guessBlock


    def query(self, parts):
        queryHex = hexlify(bytes(chain.from_iterable(parts)))
        target = self._targetURL + queryHex.decode("ascii")

        req = urllib.request.Request(target)

        try:
            status = urllib.request.urlopen(req)
        except urllib.error.URLError as e:
            status = e.code
            assert(status in (403, 404))
            return status == 404


def self_test():
    targetURL = 'http://crypto-class.appspot.com/po?er='

    target = b'f20bdba6ff29eed7b046d1df9fb7000058b1ffb4210a580f748b4ac714c001bd4a61044426fb515dad3f21f18aa577c0bdf302936266926ff37dbf7035d5eeb4'

    po = PaddingOracle(targetURL, unhexlify(target))
    pt = po.attack()

    print("Plain Text")
    print(pt.decode("ascii"))

    print("Plain Text Hex")
    print(hexlify(pt))


if __name__ == "__main__":
    self_test()
    """



import sys
import math
import gmpy2

from gmpy2 import mpz
from gmpy2 import invert
from gmpy2 import powmod
from gmpy2 import divm

def compute_x0s(p,h,g,B):
   return ((i, powmod(g, B*i, p)) for i in range(B))

def discrete_log(p, h, g, maxExp=40):
   """ Computes x such that h = g^x mod p
   """

   B = mpz(2**(int(maxExp/2)))

   g = mpz(g)
   h = mpz(h)
   p = mpz(p)

   print("Computing x1s...")
   x1s = { divm(h, powmod(g,i,p), p) : i for i in range(B) }

   print("Checking for equality...")
   for x0, exprR in compute_x0s(p,h,g,B):
       x1 = x1s.get(exprR)
       if x1 is not None:
           print("Found values!")
           print("x0 = {}".format(x0))
           print("x1 = {}".format(x1))
           return mpz(x0)*B+mpz(x1)

   raise ValueError("No suitable x0, x1 found!")

def self_test():
    p = 13407807929942597099574024998205846127479365820592393377723561443721764030073546976801874298166903427690031858186486050853753882811946569946433649006084171

    g = 11717829880366207009516117596335367088558084999998952205599979459063929499736583746670572176471460312928594829675428279466566527115212748467589894601965568

    h = 3239475104050450443565264378728065788649097520952449527834792452971981976143292558073856937958553180532878928001494706097394108577585732452307673444020333

    print("Running tiny test")
    xTiny = 3
    x = discrete_log(97, 20, 57, 6)
    print("x == {}".format(x))
    assert(xTiny == x)
    print("Tiny test passed!")
    print("")

    print("Running short test")
    xShort = 23232
    x = discrete_log(1938281, 190942, 1737373, 16)
    print("x == {}".format(x))
    assert(xShort == x)
    print("Short test passed!")
    print("")

    print("Running long test")
    x = discrete_log(p, h, g, 40)
    assert(h == powmod(g,x,p))
    print("x == {}".format(x))
    print("Long test passed!")
    print("")

if __name__ == "__main__":
    self_test()
